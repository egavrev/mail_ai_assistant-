from db_manager import get_pending_notifications
from langgraph.checkpoint.sqlite import SqliteSaver
import os
import sqlite3
from graph_processor import graph_processor

# Set up the checkpoint store (adjust path as needed)
CHECKPOINT_DB = os.environ.get("CHECKPOINT_DB", "checkpoints.sqlite")
conn = sqlite3.connect(CHECKPOINT_DB)
store = SqliteSaver(conn)


def process_pending_notifications():
    pending = get_pending_notifications()
    for notification in pending:
        checkpoint_id = notification["id"]
        # Attempt to load the checkpoint from the store
        try:
            # Namespace should match what was used for notifications
            write_config = {"configurable": {"thread_id": checkpoint_id, "checkpoint_ns": "email_notifications"}}
            checkpoint = store.get(write_config)
            print(f"Loaded checkpoint for notification id {checkpoint_id}:", checkpoint["state"]["email"]["subject"])
        except Exception as e:
            print(f"Error loading checkpoint for id {checkpoint_id}: {e}")
    states = list(graph_processor.get_state_history(write_config))

    for state in states:
        print(state.next)
        print(state.config["configurable"]["checkpoint_id"])
        print()

    

        

if __name__ == "__main__":
    process_pending_notifications() 