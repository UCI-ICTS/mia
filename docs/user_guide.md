# Mia Admin User Guide
### The following tasks are delegated to Mia administrators and developers (`Admin` role users):

### Creating and managing new participants
* Log in to https://genomics.hs.uci.edu/login with the credentials provided by the Mia administrator.
  ![image](https://github.com/user-attachments/assets/a9dece0e-607c-46ae-8ebb-c80a12e08694)
* The `Remember me` checkbox stores user information in a cookie. Without the check box, no cookie is created and page refresh will result in a logout.

* Create new study participants by navigating to the `Participants` page and clicking `Add New Participant`.
  ![image](https://github.com/user-attachments/assets/dca0efeb-5ac5-445a-91ad-d3ef9465a348)

  * The participant's first name, last name, email address, and consent script are all required fields.
  ![image](https://github.com/user-attachments/assets/56d5008d-ea7e-46a7-a907-b7c9fe5e22dc)

  * Click `Add Participant` to save changes.
    * `Edit participant` under `Actions` allows change to participant details

  #### To start the consent process, click `Actions` >  `Generate new invite link` > `Get invite link`
    * The participant's `Invite Status` should change from `Expired/DNE` in red to `Valid` in green. If not, log out and log in to refresh the table. 
  * Send the invite link to the participant to start the consent process.
  * `Consent Started` and `Consent Status` fields record participant consent status. 
  * Once a participant has completed the consent conversation, the `Consent Status` column will read `Complete` in green.

### Participant follow-up.
  * If a participant requests study staff followup, their entry will show up in the `Participant Follow Up` page under the `Admin` panel.
  * If a participant chooses not to provide consent, their `Consent Status` should read `Did not consent to the genetics study`.
 
### Participant deletion after withdrawl of consent.
  * If a participant requests to withdraw consent, they may be deleted. 
  * To delete a participant, click on the `Delete participant` button under `Actions`.
  * **🔴 Warning:** This action will result in perminent, irreversable deletion.

### List of Scripts. 
  ![image](https://github.com/user-attachments/assets/9b5adf32-c93f-49f6-ad48-231f45b06363)

  * For example, a GREGoR consent script is stored in this repository's `docs/PMGRC_Consent.json`.
  * Editing the file will not change the script uploaded to the Mia website.
  * Changes should only happen in accordance with new project deployment or IRB review. 

### Manage Admin Users page for name, email, and password reset. 
  ![image](https://github.com/user-attachments/assets/789c616b-06d5-42e3-aefe-fda198895f85)
