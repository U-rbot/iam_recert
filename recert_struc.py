import streamlit as st
import pandas as pd
from io import BytesIO
import datetime

# Function to read data from Excel
def load_data(file_path):
    df = pd.read_excel(file_path)
    return df

# Function to save data to Excel
def save_data(df, file_path):
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

# Function to save decisions to session state
def save_decisions(decisions):
    st.session_state['decisions'] = decisions

# Function to retrieve decisions from session state
def get_decisions():
    return st.session_state.get('decisions', {})

# Function to log actions for audit purposes
def log_action(action, user, details):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {action}: {user} - {details}"
    st.write(log_entry)  # Replace with actual logging mechanism

# Main function
def main():
    st.title('Access Recertification Review')
    st.write('Review and manage user access rights.')

    # Upload Excel file
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    if uploaded_file is not None:
        df = load_data(uploaded_file)

        # Display tabs for Open (Pending Items) and Completed (Reviewed Items)
        tabs = st.tabs(["Open (Pending Items)", "Completed (Reviewed Items)"])

        with tabs[0]:
            display_pending_items(df, uploaded_file.name)
        with tabs[1]:
            display_completed_items(df, uploaded_file.name)

# Function to display pending items
def display_pending_items(df, file_path):
    st.header('Open (Pending Items)')

    # Filtered DataFrame for pending items
    pending_df = df[df['Status'] == 'Pending']

    # Display table for pending items with decision options
    if not pending_df.empty:
        st.write("### Pending Items")
        decisions = get_decisions()

        # Table headers
        cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2])
        headers = ["Record ID", "User", "User ID", "Access Right", "Account Type", "Department", "Cost Center", "Manager", "Email ID", "Employee Status", "Decision", "Comment"]
        for col, header in zip(cols, headers):
            col.write(f"**{header}**")

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

            decision_value = cols[10].selectbox('', options=['', 'Approve', 'Revoke'], key=decision_key, index=0 if decision_value == "" else ['', 'Approve', 'Revoke'].index(decision_value))
            comment_value = cols[11].text_input('', key=comment_key, value=comment_value if decision_value == 'Revoke' else "", disabled=decision_value != 'Revoke')

            decisions[decision_key] = decision_value
            decisions[comment_key] = comment_value

        save_decisions(decisions)

        # Save and clear decisions
        actions_col1, actions_col2 = st.columns([1, 1])
        if actions_col1.button('Save Decisions'):
            for index, row in pending_df.iterrows():
                record_id = row['Record_ID']
                decision_key = f"decision_{record_id}"
                comment_key = f"comment_{record_id}"

                if decisions.get(decision_key) == 'Approve':
                    df.loc[df['Record_ID'] == record_id, 'Status'] = 'Approved'
                elif decisions.get(decision_key) == 'Revoke':
                    df.loc[df['Record_ID'] == record_id, 'Status'] = 'Revoked'
                    df.loc[df['Record_ID'] == record_id, 'Comment'] = decisions.get(comment_key, '')

            save_data(df, file_path)
            st.success('Decisions saved.')
            log_action('Save Decisions', 'Reviewer', 'Saved decisions for pending items.')

        if actions_col2.button('Clear Decisions'):
            st.session_state['decisions'] = {}
            st.success('Decisions cleared.')
            log_action('Clear Decisions', 'Reviewer', 'Cleared decisions.')

        # Bulk actions
        st.subheader('Bulk Actions')
        bulk_actions_col1, bulk_actions_col2 = st.columns([1, 1])
        if bulk_actions_col1.button('Bulk Approve'):
            for index, row in pending_df.iterrows():
                df.loc[df['Record_ID'] == row['Record_ID'], 'Status'] = 'Approved'
            save_data(df, file_path)
            st.success('All pending items approved.')
            log_action('Bulk Approve', 'Reviewer', 'Bulk approved all pending items.')

        if bulk_actions_col2.button('Bulk Revoke'):
            for index, row in pending_df.iterrows():
                df.loc[df['Record_ID'] == row['Record_ID'], 'Status'] = 'Revoked'
            save_data(df, file_path)
            st.success('All pending items revoked.')
            log_action('Bulk Revoke', 'Reviewer', 'Bulk revoked all pending items.')

# Function to display completed items
def display_completed_items(df, file_path):
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
        is_valid, message = validate_decisions(decisions, completed_df)

        if not is_valid:
            st.error(message)
        else:
            for index, row in completed_df.iterrows():
                record_id = row['Record_ID']
                decision_key = f"decision_{record_id}"
                comment_key = f"comment_{record_id}"

                if decisions.get(decision_key) == 'Approve':
                    df.loc[df['Record_ID'] == record_id, 'Status'] = 'Next Approved'
                elif decisions.get(decision_key) == 'Revoke':
                    df.loc[df['Record_ID'] == record_id, 'Status'] = 'Next Revoked'
                    df.loc[df['Record_ID'] == record_id, 'Comment'] = decisions.get(comment_key, '')

            save_data(df, file_path)
            st.success('Next sign-off decision saved.')
            log_action('Next Sign-off Decision', 'Reviewer', 'Saved next sign-off decision for completed items.')

# Run the main function
if __name__ == "__main__":
    main()
