This guide is for Mia users engaged in the following tasks:
* Creating and managing study participants.
* Forwarding completed consents to study staff.
* Forwarding participant questions to study staff.
* Editing and uploading new chatbot scripts for new studies.

The following tasks are delegated to Mia administrators and developers (`Admin` role users):
* Managing and collecting participant metrics from the Mia database.
* Creating and administering new users.

Creating and managing new participants
* Log in to https://genomics.hs.uci.edu/login with the credentials provided by the Mia administrator.
  ![image](https://github.com/user-attachments/assets/a9dece0e-607c-46ae-8ebb-c80a12e08694)
* The `Remember me` checkbox stores your information in a cookie. Without the check box, no cookie is created and page refresh will result in a logout.

*  `Manage Admin Users` page for name, email, and password reset. 
  ![image](https://github.com/user-attachments/assets/789c616b-06d5-42e3-aefe-fda198895f85)

* List of Scripts. 
  ![image](https://github.com/user-attachments/assets/9b5adf32-c93f-49f6-ad48-231f45b06363)

  * For example, a GREGoR consent script is stored in this repository's `docs/PMGRC_Consent.json`.
  * Editing the file will not change the script uploaded to the Mia website.

* Create new study participants by navigating to the `Participants` page and clicking `Add New Participant`.
  ![image](https://github.com/user-attachments/assets/dca0efeb-5ac5-445a-91ad-d3ef9465a348)

  * The participant's first name, last name, email address, and consent script are all required fields.
  ![image](https://github.com/user-attachments/assets/56d5008d-ea7e-46a7-a907-b7c9fe5e22dc)

  * Click `Add Participant` to save changes.
    * If any changes need to be made to a participant's details, edit them with the `Edit participant` button under the `Actions` column.

  * To start the consenting process, on the right-most column under `Actions`, click `Generate new invite link`, followed by `Get invite link`.
    * The participant's `Invite Status` should change from `Expired/DNE` in red to `Valid` in green. If not, log out and log in to refresh the table. 
  * Forward the invite link to the participant by email to start the consenting process.
  * A participant's consenting process can be monitored from the `Consent Started` and `Consent Status` columns. 
  * Once a participant has completed their consent form, the `Consent Status` column should read `Complete` in green.
  * Forward their consent to the study's CRC to begin collecting phenotypic data by means outside of Mia.

  * If a participant requests to follow up with a CRC, their entry will show up in the `Participant Follow Up` page under the `Admin` panel.
  * If a participant chooses not to provide consent, their `Consent Status` should read ``.
 
  * For deleting a participant, refer to study procedures for determining when this is appropriate.
    * To delete a participant, click on the `Delete participant` button under `Actions`.
      * There is no undoing this so be absolutely certain.

This covers all of the general functions of Mia. If you have any questions, concerns, bug reports, please file a new issue following the relevant templates in this GitHub repository.
