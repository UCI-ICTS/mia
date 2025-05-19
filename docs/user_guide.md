This guide is intended for users who use Mia for the following tasks:
* Creating and managing study (UCI-GREGoR) enrollees/participants for the purpose of collecting their consent as a `Staff` role user.
* Forwarding completed consents to clinical research coordinators (CRCs).
* Forwarding any follow-up questions from enrollees to CRCs.
* Deleting enrollees who have either chosen not to provide their consent to the study or abandoned their chatbot session for an excessive amount of time.
* Editing and uploading new chatbot scripts for new studies such as UDN. Currently only the PMGRC chatbot script is available for consenting.

The following tasks are delegated to Mia administrators and developers (`Admin` role users):
* Managing and collecting enrollee metrics from the Mia database.
  * This can include their first quiz attempt scores and which specific questions they answered correctly/incorrectly.
* Creating and administering new users/CRCs.

General notes about using the Mia webpage:
* Avoid refreshing the page with F5 or from outside the webpage.
  * Doing so will log you out and you risk losing any unsaved work.

Creating and managing new study participants
* Log in to https://genomics.hs.uci.edu/login with the credentials provided by the Mia administrator.
  ![image](https://github.com/user-attachments/assets/a9dece0e-607c-46ae-8ebb-c80a12e08694)
  * Eventually a `Forgot password` feature will be available on the login page but until then, use the web interface to change your password.

* On the left `Admin` panel, you can change your name, email, and password from `Manage Admin Users` page.
  ![image](https://github.com/user-attachments/assets/789c616b-06d5-42e3-aefe-fda198895f85)

* Check if the required consentbot script is available from the `Consentbot Scripts` page.
  ![image](https://github.com/user-attachments/assets/9b5adf32-c93f-49f6-ad48-231f45b06363)

  * The PMGRC consent script is stored in this repository's `docs/PMGRC_Consent.json`.
  * Editing the file will not change the script uploaded to the Mia website.
  * Feel free to edit the JSON in your favorite code editor such as VSCode, for the purposes of updating an existing consent chatbot script or creating a new one. 

* Create new study enrollees by navigating to the `Participants` page and clicking `Add New Participant`.
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
