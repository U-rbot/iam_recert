import streamlit as st
import pandas as pd
from io import BytesIO
import datetime

# Sample data for demonstration
data = {
    'Record_ID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'User': ['User1', 'User2', 'User3', 'User4', 'User5', 'User6', 'User7', 'User8', 'User9', 'User10'],
    'User_ID': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    'Access_Right': ['Admin', 'Editor', 'Viewer', 'Editor', 'Admin', 'Viewer', 'Editor', 'Admin', 'Viewer', 'Editor'],
    'Account_Type': ['Generic', 'Standard', 'Generic', 'Standard', 'Generic', 'Standard', 'Generic', 'Standard', 'Generic', 'Standard'],
    'Department': ['HR', 'Finance', 'IT', 'HR', 'Finance', 'IT', 'HR', 'Finance', 'IT', 'HR'],
    'Cost_Center': ['CC1', 'CC2', 'CC3', 'CC4', 'CC5', 'CC6', 'CC7', 'CC8', 'CC9', 'CC10'],
    'Manager': ['Manager1', 'Manager2', 'Manager3', 'Manager4', 'Manager5', 'Manager6', 'Manager7', 'Manager8', 'Manager9', 'Manager10'],
    'Email_ID': ['user1@example.com', 'user2@example.com', 'user3@example.com', 'user4@example.com', 'user5@example.com', 'user6@example.com', 'user7@example.com', 'user8@example.com', 'user9@example.com', 'user10@example.com'],
    'Employee_Status': ['Active', 'Active', 'Active', 'Active', 'Active', 'Active', 'Active', 'Active', 'Active', 'Active'],
    'Status': ['Pending'] * 10,
    'Decision': [''] * 10,
    'Comment': [''] * 10,
}

# Convert data to DataFrame
df = pd.DataFrame(data)

# Function to save decisions to session state
def save_decisions(decisions):
    st.session_state['decisions'] = decisions

# Function to retrieve decisions from session state
def get_decisions():
    return st.session_state.get('decisions', {})

# Function to validate decisions
def validate_decisions(decisions, df):
    for index, row in df.iterrows():
        record_id = row['Record_ID']
        decision_key = f"decision_{record_id}"
        comment_key = f"comment_{record_id}"
        if decisions.get(decision_key) == 'Revoke' and not decisions.get(comment_key):
            return False, f"Comment required for revoking access of Record ID {record_id}"
    return True, ""

# Function to convert DataFrame to Excel format
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

# Function to log actions for audit purposes
def log_action(action, user, details):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {action}: {user} - {details}"
    st.write(log_entry)  # Replace with actual logging mechanism

# Main function
def main():
    st.title('Access Recertification Review')
    st.write('Review and manage user access rights.')

    # Display tabs for Open (Pending Items) and Completed (Reviewed Items)
    tabs = st.tabs(["Open (Pending Items)", "Completed (Reviewed Items)"])

    with tabs[0]:
        display_pending_items()
    with tabs[1]:
        display_completed_items()

# Function to display pending items
def display_pending_items():
    st.header('Open (Pending Items)')

    # Filtered DataFrame for pending items
    pending_df = df[df['Status'] == 'Pending']

    # Display table for pending items with decision options
    if not pending_df.empty:
        st.write("### Pending Items")
        decisions = get_decisions()

        # Table headers
        cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2])
        cols[0].write("Record ID")
        cols[1].write("User")
        cols[2].write("User ID")
        cols[3].write("Access Right")
        cols[4].write("Account Type")
        cols[5].write("Department")
        cols[6].write("Cost Center")
        cols[7].write("Manager")
        cols[8].write("Email ID")
        cols[9].write("Employee Status")
        cols[10].write("Decision")
        cols[11].write("Comment")

        for index, row in pending_df.iterrows():
            record_id = row['Record_ID']
            decision_key = f"decision_{record_id}"
            comment_key = f"comment_{record_id}"

            decision_value = decisions.get(decision_key, "")
            comment_value = decisions.get(comment_key, "")

            cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2])
            cols[0].write(row['Record_ID'])
            cols[1].write(row['User'])
            cols[2].write(row['User_ID'])
            cols[3].write(row['Access_Right'])
            cols[4].write(row['Account_Type'])
            cols[5].write(row['Department'])
            cols[6].write(row['Cost_Center'])
            cols[7].write(row['Manager'])
            cols[8].write(row['Email_ID'])
            cols[9].write(row['Employee_Status'])

            decision_value = cols[10].selectbox('Decision', options=['', 'Approve', 'Revoke'], key=decision_key, index=0 if decision_value == "" else ['', 'Approve', 'Revoke'].index(decision_value))
            comment_value = cols[11].text_input('Comment', key=comment_key, value=comment_value if decision_value == 'Revoke' else "", disabled=decision_value != 'Revoke')

            decisions[decision_key] = decision_value
            decisions[comment_key] = comment_value

        save_decisions(decisions)

        # Save and clear decisions
        action_cols = st.columns([2, 2, 1])
        if action_cols[0].button('Save Decisions'):
            for index, row in pending_df.iterrows():
                record_id = row['Record_ID']
                decision_key = f"decision_{record_id}"
                comment_key = f"comment_{record_id}"

                if decisions.get(decision_key) == 'Approve':
                    df.loc[df['Record_ID'] == record_id, 'Status'] = 'Approved'
                elif decisions.get(decision_key) == 'Revoke':
                    df.loc[df['Record_ID'] == record_id, 'Status'] = 'Revoked'
                    df.loc[df['Record_ID'] == record_id, 'Comment'] = decisions.get(comment_key, '')

            st.success('Decisions saved.')
            log_action('Save Decisions', 'Reviewer', 'Saved decisions for pending items.')

        if action_cols[1].button('Clear Decisions'):
            st.session_state['decisions'] = {}
            st.success('Decisions cleared.')
            log_action('Clear Decisions', 'Reviewer', 'Cleared decisions.')

        # Bulk actions
        st.subheader('Bulk Actions')
        bulk_action_cols = st.columns([2, 2, 1])
        if bulk_action_cols[0].button('Bulk Approve'):
            for index, row in pending_df.iterrows():
                df.loc[df['Record_ID'] == row['Record_ID'], 'Status'] = 'Approved'
            st.success('All pending items approved.')
            log_action('Bulk Approve', 'Reviewer', 'Bulk approved all pending items.')

        if bulk_action_cols[1].button('Bulk Revoke'):
            for index, row in pending_df.iterrows():
                df.loc[df['Record_ID'] == row['Record_ID'], 'Status'] = 'Revoked'
            st.success('All pending items revoked.')
            log_action('Bulk Revoke', 'Reviewer', 'Bulk revoked all pending items.')

# Function to display completed items
def display_completed_items():
    st.header('Completed (Reviewed Items)')

    # Filtered DataFrame for completed items
    completed_df = df[df['Status'] != 'Pending']

    # Display table for completed items
    if not completed_df.empty:
        st.dataframe(completed_df)

    # Clear decisions for completed items
    if st.button('Clear Decisions', key="clear_decisions_completed"):
        st.session_state['decisions'] = {}
        st.success('Decisions cleared for reviewed items.')
        log_action('Clear Decisions', 'Reviewer', 'Cleared decisions for reviewed items.')

    # Next sign-off decision for completed items
    if st.button('Next Sign-off Decision', key="next_sign_off_decision"):
        decisions = get_decisions()
        is_valid, validation_message = validate_decisions(decisions, completed_df)

        if not is_valid:
            st.error(validation_message)
            return

        for index, row in completed_df.iterrows():
            record_id = row['Record_ID']
            decision_key = f"decision_{record_id}"
            comment_key = f"comment_{record_id}"

            if decisions.get(decision_key) == 'Approve':
                df.loc[df['Record_ID'] == record_id, 'Status'] = 'Next Approved'
            elif decisions.get(decision_key) == 'Revoke':
                df.loc[df['Record_ID'] == record_id, 'Status'] = 'Next Revoked'
                df.loc[df['Record_ID'] == record_id, 'Comment'] = decisions.get(comment_key, '')

        st.success('Next sign-off decision saved.')
        log_action('Next Sign-off Decision', 'Reviewer', 'Saved next sign-off decision for reviewed items.')

# Run the main function
if __name__ == "__main__":
    main()
