import streamlit as st
import pandas as pd
from io import BytesIO
import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# Sample data for demonstration
data = {
    'Record_ID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'User': ['User1', 'User2', 'User3', 'User4', 'User5', 'User6', 'User7', 'User8', 'User9', 'User10'],
    'User ID': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    'Access Right': ['Admin', 'Editor', 'Viewer', 'Editor', 'Admin', 'Viewer', 'Editor', 'Admin', 'Viewer', 'Editor'],
    'Account Type': ['Generic', 'Standard', 'Generic', 'Standard', 'Generic', 'Standard', 'Generic', 'Standard', 'Generic', 'Standard'],
    'Department': ['HR', 'Finance', 'IT', 'HR', 'Finance', 'IT', 'HR', 'Finance', 'IT', 'HR'],
    'Status': ['Pending'] * 10,
    'Comment': [''] * 10,
}

# Convert data to DataFrame
df = pd.DataFrame(data)

# Function to load data for access recertification review
def load_data():
    return df

# Function to save decisions to session state
def save_decisions(decisions):
    st.session_state['decisions'] = decisions

# Function to retrieve decisions from session state
def get_decisions():
    return st.session_state.get('decisions', {})

# Function to validate decisions
def validate_decisions(decisions, df):
    for index, row in df.iterrows():
        revoke_key = f"revoke_{row['Record_ID']}"
        comment_key = f"comment_{row['Record_ID']}"
        if decisions.get(revoke_key) and not decisions.get(comment_key):
            return False, f"Comment required for revoking access of Record ID {row['Record_ID']}"
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
    st.write(log_entry)  # For demonstration, replace with actual logging mechanism

# Function to authenticate reviewer (replace with your implementation)
def authenticate_reviewer():
    # Replace this with your actual authentication logic (e.g., username/password, token)
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    # Simulate authentication (replace with your validation)
    return username == 'reviewer' and password == 'reviewer_password'

# Main function
def main():
    st.title('Access Recertification Review')
    st.write('Review and manage user access rights.')

    # Authentication
    if not authenticate_reviewer():
        st.error('Access denied. Please sign in as a reviewer.')
        return

    # Tabs for different review stages
    tab1, tab2, tab3 = st.tabs(['Pending Review', 'Decisions Applied', 'Final Sign Off'])

    # Search bar
    search_query = st.text_input('Search users or access items')

    # Filter options
    role_filter = st.selectbox('Filter by role', options=['All'] + df['Access Right'].unique().tolist())
    department_filter = st.selectbox('Filter by department', options=['All'] + df['Department'].unique().tolist())

    def display_review(df_stage):
        # Apply search and filter
        df_filtered = df_stage.copy()
        if search_query:
            df_filtered = df_filtered[df_filtered['User'].str.contains(search_query, case=False)]
        if role_filter != 'All':
            df_filtered = df_filtered[df_filtered['Access Right'] == role_filter]
        if department_filter != 'All':
            df_filtered = df_filtered[df_filtered['Department'] == department_filter]

        decisions = get_decisions()

        # Update decisions from previous state
        for index, row in df_filtered.iterrows():
            record_id = row['Record_ID']
            approve_key = f"approve_{record_id}"
            revoke_key = f"revoke_{record_id}"
            comment_key = f"comment_{record_id}"
            df_filtered.at[index, 'Approve'] = decisions.get(approve_key, False)
            df_filtered.at[index, 'Revoke'] = decisions.get(revoke_key, False)
            df_filtered.at[index, 'Comment'] = decisions.get(comment_key, '')

        # Custom cell renderer for approve and revoke buttons
        cell_renderer = JsCode('''
        class BtnCellRenderer {
            init(params) {
                this.params = params;

                // Approve button
                const approveBtn = document.createElement('span');
                approveBtn.innerHTML = '👍';
                approveBtn.style.cursor = 'pointer';
                approveBtn.style.marginRight = '5px';
                approveBtn.addEventListener('click', this.onApprove.bind(this));

                // Revoke button
                const revokeBtn = document.createElement('span');
                revokeBtn.innerHTML = '👎';
                revokeBtn.style.cursor = 'pointer';
                revokeBtn.addEventListener('click', this.onRevoke.bind(this));

                this.eGui = document.createElement('div');
                this.eGui.appendChild(approveBtn);
                this.eGui.appendChild(revokeBtn);
            }

            getGui() {
                return this.eGui;
            }

            onApprove() {
                const approve_key = `approve_${this.params.data.Record_ID}`;
                this.params.api.stopEditing();
                this.params.node.setDataValue('Approve', true);
                this.params.node.setDataValue('Revoke', false);
                window.dispatchEvent(new CustomEvent('approve', { detail: approve_key }));
            }

            onRevoke() {
                const revoke_key = `revoke_${this.params.data.Record_ID}`;
                this.params.api.stopEditing();
                this.params.node.setDataValue('Approve', false);
                this.params.node.setDataValue('Revoke', true);
                window.dispatchEvent(new CustomEvent('revoke', { detail: revoke_key }));
            }
        }
        ''')

        gb = GridOptionsBuilder.from_dataframe(df_filtered)
        gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
        gb.configure_default_column(editable=True, groupable=True, sortable=True, filter=True)
        gb.configure_column('Actions', cellRenderer=cell_renderer, editable=False)
        gb.configure_column('Approve', hide=True)
        gb.configure_column('Revoke', hide=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            df_filtered,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True,
            enable_enterprise_modules=True,
            height=400,
            width='100%',
        )

        # Capture changes
        new_df = grid_response['data']

        for index, row in new_df.iterrows():
            record_id = row['Record_ID']
            approve_key = f"approve_{record_id}"
            revoke_key = f"revoke_{record_id}"
            comment_key = f"comment_{record_id}"
            decisions[approve_key] = row['Approve']
            decisions[revoke_key] = row['Revoke']
            decisions[comment_key] = row['Comment']

        # Save progress
        if st.button('Save Decisions'):
            save_decisions(decisions)

            # Move approved/revoked items to the Decisions Applied tab
            for index, row in new_df.iterrows():
                if row['Approve'] or row['Revoke']:
                    df.loc[df['Record_ID'] == row['Record_ID'], 'Status'] = 'Approved' if row['Approve'] else 'Revoked'
                    df.loc[df['Record_ID'] == row['Record_ID'], 'Comment'] = row['Comment']

            st.success('Decisions saved as draft.')
            log_action('Save Decisions', 'Reviewer', 'Saved draft decisions.')

        # Clear decisions
        if st.button('Clear Decisions'):
            st.session_state['decisions'] = {}
            st.success('Decisions cleared.')
            log_action('Clear Decisions', 'Reviewer', 'Cleared all decisions.')

    with tab1:
        st.header("Pending Review")
        display_review(load_data()[load_data()['Status'] == 'Pending'])

    with tab2:
        st.header("Decisions Applied")
        display_review(load_data()[load_data()['Status'] != 'Pending'])

    with tab3:
        st.header("Final Sign Off")
        display_review(load_data())

        # Sign off button with confirmation
        if st.button('Sign Off'):
            decisions = get_decisions()
            is_valid, message = validate_decisions(decisions, load_data())

            if not is_valid:
                st.error(message)
            else:
                if st.confirm('Are you sure you want to sign off on all access items?'):
                    for index, row in load_data().iterrows():
                        record_id = row['Record_ID']
                        approve_key = f"approve_{record_id}"
                        revoke_key = f"revoke_{record_id}"
                        comment_key = f"comment_{record_id}"
                        if decisions.get(approve_key) or decisions.get(revoke_key):
                            df.loc[df['Record_ID'] == record_id, 'Status'] = 'Approved' if decisions.get(approve_key) else 'Revoked'
                            df.loc[df['Record_ID'] == record_id, 'Comment'] = decisions.get(comment_key, '')
                    st.success('All access items reviewed and signed off.')
                    log_action('Sign Off', 'Reviewer', 'Signed off all access items.')

        # Download report with error handling
        if st.button('Download Report'):
            try:
                report = df[['Record_ID', 'User', 'User ID', 'Access Right', 'Account Type', 'Status', 'Comment']]
                report_data = to_excel(report)
                st.download_button(label='Download Report', data=report_data, file_name='access_review_report.xlsx')
                log_action('Download Report', 'Reviewer', 'Downloaded access review report.')
            except Exception as e:
                st.error(f"Error generating report: {e}")

    # Summary and history sections
    st.subheader('Access Summary')
    access_summary = df.groupby(['Access Right', 'Status']).size().reset_index(name='Count')
    st.table(access_summary)

    st.subheader('Review History')
    review_history = df[['Record_ID', 'User', 'Access Right', 'Status', 'Comment']]
    st.table(review_history)

if __name__ == "__main__":
    main()
