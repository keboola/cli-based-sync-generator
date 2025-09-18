
## Github Repository Initialization


1. Download generated Github Actions zip file using the button above.
2. Create and pull github repository.
3. Unpack the `git_actions.zip` in the repository root folder
   - This will create a `.github` actions folder, overwrite if it exists.
4. Run the following commands:
    1. `git add .`
    2. `git commit -m "Initial commit"`
    3. `git push`
5. Create long-lived git branches for your environment.
    {branch_table}
6. Commit and push to each created branch.
    - This step may be skipped if perform KBC PULL first on the main branch and then create branches in the Github 
   repository off that one.
7. In the repository [settings](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#creating-an-environment), create the following environments:
    {env_list}

<p align="center">
    <img src="data:image/png;base64,{git_env_setup_img_path}" alt="git_env_setup_img_path" width="600">
</p>


8. You may set the ENV restrictions
   - Note that the github actions need access to both related environments (DEV/PROD) in order to perform comparison 
   validations.

<p align="center">
    <img src="data:image/png;base64,{branch_protection_img_path}" alt="branch_protection_img_path" width="600">
</p>


9. For each environment set the following: 


### Environment Secrets:

Set the following secrets in your repository environments:


{env_secrets_table}


### Environment variables

Set the following variables in your repository environments:

{env_variables_table}


## Perform initial sync


1. Go to `Repository > Actions`
2. Click on action **Manual KBC Pull**
    1. Select branch `main` and hit run
    2. Optionally Select destination branch
        1. When selected validations against the selected environment projects will be run.

<p align="center">
    <img src="data:image/png;base64,{git_action_img_path}" alt="action" width="450">
</p>

3. Create other branches off the main branch
4. For each branch (except production) run **Manual KBC Push**
