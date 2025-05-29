import os
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_AI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", temperature=0)


# ==============================================================================
# EMAIL FUNCTIONS (Direct, no agent)
# ==============================================================================

def dummy_send_email(to: str, subject: str, body: str):
    print(f"\n📧 Sending email to: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}\n")
    return 1


def send_direct_email(subject: str, body: str) -> str:
    """Send email directly without using another agent"""
    recipient = "ops-team@example.com"
    result = dummy_send_email(to=recipient, subject=subject, body=body)
    if result == 0:
        return f"❌ TASK FAILED: Email NOT Sent. TRY AGAIN."
    return f"✅ TASK COMPLETED: Email successfully sent to {recipient} with subject '{subject}'. No further action needed."


# ==============================================================================
# DATABASE MONITORING AGENT
# ==============================================================================

# Dummy database status simulation
DATABASES = {
    "db-prod-1": {"status": "up", "last_check": None},
    "db-prod-2": {"status": "up", "last_check": None},
    "db-staging-1": {"status": "up", "last_check": None},
    "db-analytics": {"status": "up", "last_check": None},
    "db-cache": {"status": "up", "last_check": None}
}

# Track sent alerts to prevent duplicates
sent_alerts = set()


def dummy_check_database(db_name: str) -> dict:
    """Simulate database health check with random failures"""
    # 30% chance of downtime for testing
    is_down = random.random() < 0.3
    status = "down" if is_down else "up"

    check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if is_down:
        failure_reasons = [
            "Connection timeout",
            "High CPU usage (>90%)",
            "Disk space full",
            "Memory leak detected",
            "Network connectivity issues",
            "Authentication failure"
        ]
        reason = random.choice(failure_reasons)
    else:
        reason = "Operating normally"

    return {
        "database": db_name,
        "status": status,
        "reason": reason,
        "check_time": check_time,
        "response_time_ms": random.randint(10, 500) if status == "up" else None
    }


@tool
def check_all_databases() -> str:
    """Check the status of all monitored databases.

    Returns:
        Summary of all database statuses with down databases clearly identified
    """
    results = []
    down_databases = []

    for db_name in DATABASES.keys():
        result = dummy_check_database(db_name)
        DATABASES[db_name]["status"] = result["status"]
        DATABASES[db_name]["last_check"] = result["check_time"]

        if result["status"] == "down":
            results.append(f"🚨 {db_name}: DOWN ({result['reason']})")
            down_databases.append({
                "name": db_name,
                "reason": result["reason"],
                "time": result["check_time"]
            })
        else:
            results.append(f"✅ {db_name}: UP ({result['response_time_ms']}ms)")

    summary = "DATABASE STATUS SUMMARY:\n" + "\n".join(results)

    if down_databases:
        summary += f"\n\n⚠️ CRITICAL: {len(down_databases)} database(s) are down!"
        summary += "\nDOWN DATABASES:"
        for db in down_databases:
            summary += f"\n- {db['name']}: {db['reason']} (at {db['time']})"
    else:
        summary += "\n\n✅ ALL DATABASES ARE OPERATIONAL"

    return summary


@tool
def send_consolidated_alert_email() -> str:
    """Send a single consolidated alert email for all down databases.

    Returns:
        Result of the email sending operation
    """
    # Get current down databases
    down_databases = []
    for db_name, db_info in DATABASES.items():
        if db_info.get("status") == "down":
            down_databases.append({
                "name": db_name,
                "time": db_info.get("last_check", "Unknown")
            })

    if not down_databases:
        return "ℹ️ No down databases found. No alert email needed."

    # Create alert key to prevent duplicate sends
    alert_key = "-".join([db["name"] for db in down_databases])

    if alert_key in sent_alerts:
        return f"ℹ️ Alert already sent for these databases: {[db['name'] for db in down_databases]}"

    # Build consolidated email
    if len(down_databases) == 1:
        subject = f"🚨 CRITICAL: Database {down_databases[0]['name']} is DOWN"
        body = f"""ALERT: Database Downtime Detected

Database: {down_databases[0]['name']}
Status: DOWN
Detected at: {down_databases[0]['time']}

Please investigate immediately and take necessary action to restore service.

This is an automated alert from the Database Monitoring System."""
    else:
        subject = f"🚨 CRITICAL: Multiple Databases DOWN ({len(down_databases)} affected)"
        body = f"""ALERT: Multiple Database Failures Detected

AFFECTED DATABASES ({len(down_databases)}):
"""
        for db in down_databases:
            body += f"- {db['name']} (detected at {db['time']})\n"

        body += """
Please investigate immediately and take necessary action to restore services.

This is an automated alert from the Database Monitoring System."""

    try:
        # Send email directly (no agent call)
        result = send_direct_email(subject=subject, body=body)

        # Mark alert as sent
        sent_alerts.add(alert_key)

        return f"✅ ALERT EMAIL SENT: Consolidated alert sent for {len(down_databases)} database(s). {result}"
    except Exception as e:
        return f"❌ Failed to send consolidated alert email: {str(e)}"


monitoring_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a Database Monitoring Agent. Your job is simple and clear:

PROCESS:
1. Use check_all_databases tool to check all database statuses
2. If ANY databases are down, use send_consolidated_alert_email tool ONCE
3. Report the monitoring results and STOP

RULES:
- Check databases first, always
- Send only ONE consolidated email for all down databases
- Do NOT send multiple emails
- Do NOT repeat actions
- Once email is sent (or no email needed), your task is COMPLETE

Be efficient and stop after completing the monitoring and alerting process.
"""),
    ("user", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

monitoring_agent = create_openai_functions_agent(
    llm=llm,
    tools=[check_all_databases, send_consolidated_alert_email],
    prompt=monitoring_prompt
)

monitoring_executor = AgentExecutor(
    agent=monitoring_agent,
    tools=[check_all_databases, send_consolidated_alert_email],
    verbose=True,
    max_execution_time=45,
    max_iterations=5,  # Limit iterations to prevent loops
    return_intermediate_steps=True
)


# ==============================================================================
# STANDALONE EMAIL AGENT (for manual email sending)
# ==============================================================================

@tool
def send_fixed_email(subject: str, body: str) -> str:
    """Send an email to a fixed recipient address with the given subject and body.
    Args:
        subject: Email subject line
        body: Email body content
    Returns:
        Confirmation message when email is sent successfully.
    """
    return send_direct_email(subject=subject, body=body)


email_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an assistant that sends status update or alert emails to ops-team@example.com.
INSTRUCTIONS:
1. Extract the subject and body from the user's message
2. Send exactly ONE email using the send_fixed_email tool
3. Once the email is sent successfully, provide a brief confirmation and STOP
4. DO NOT ask for additional information - work with what's provided
The email address is fixed at ops-team@example.com and not part of user input.
"""),
    ("user", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

email_agent = create_openai_functions_agent(
    llm=llm,
    tools=[send_fixed_email],
    prompt=email_prompt
)

email_executor = AgentExecutor(
    agent=email_agent,
    tools=[send_fixed_email],
    verbose=True,
    max_execution_time=30,
    max_iterations=3,  # Limit iterations for email agent
    return_intermediate_steps=True
)


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def run_monitoring_cycle():
    """Run a single monitoring cycle"""
    print("\n" + "=" * 60)
    print("🔍 STARTING DATABASE MONITORING CYCLE")
    print("=" * 60)

    # Clear previous alerts for new cycle
    global sent_alerts
    sent_alerts.clear()

    try:
        response = monitoring_executor.invoke({
            "input": "Check all databases and send alert email if any are down"
        })
        print("\n✅ Monitoring cycle completed successfully")
        return response
    except Exception as e:
        print(f"\n❌ Monitoring cycle failed: {e}")
        return None


def run_continuous_monitoring(cycles=3, interval=10):
    """Run continuous monitoring for a specified number of cycles"""
    print(f"\n🚀 Starting continuous database monitoring ({cycles} cycles, {interval}s interval)")

    for cycle in range(1, cycles + 1):
        print(f"\n📊 CYCLE {cycle}/{cycles}")
        run_monitoring_cycle()

        if cycle < cycles:
            print(f"\n⏳ Waiting {interval} seconds before next check...")
            time.sleep(interval)

    print("\n🏁 Monitoring session completed!")


if __name__ == "__main__":
    print("DATABASE MONITORING & ALERTING SYSTEM")
    print("=" * 50)

    # Single monitoring check
    print("\nRunning database monitoring check...")
    run_monitoring_cycle()

    # Uncomment for continuous monitoring
    # print("\nRunning continuous monitoring...")
    # run_continuous_monitoring(cycles=3, interval=5)