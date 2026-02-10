# SSH Configuration for GitLab CI/CD

This guide explains how to generate an SSH key pair and configure it to allow GitLab to deploy code to your Raspberry Pi.

## 1. Generate SSH Key Pair
Run this command in your local terminal (not on the Pi):

```bash
ssh-keygen -t ed25519 -C "gitlab-ci" -f ./gitlab_deploy_key
```

- When asked for a passphrase, **leave it empty** (press Enter twice).
- This will create two files in your current directory:
    - `gitlab_deploy_key` (The **Private Key** - Keep this secret!)
    - `gitlab_deploy_key.pub` (The **Public Key**)

## 2. Add Public Key to Raspberry Pi
You need to put the *public* key onto your Raspberry Pi so it accepts connections using the private key.

1.  **Copy the content** of `gitlab_deploy_key.pub`.
2.  **SSH into your Raspberry Pi**:
    ```bash
    ssh pi@<your-pi-ip>
    ```
3.  **Add to authorized_keys**:
    Run these commands on the Pi:
    ```bash
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    echo "PASTE_YOUR_PUBLIC_KEY_CONTENT_HERE" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    ```
    *(Replace `PASTE_YOUR_PUBLIC_KEY_CONTENT_HERE` with the actual text from `gitlab_deploy_key.pub`)*

## 3. Add Private Key to GitLab
Now give GitLab the *private* key so it can authenticate as you.

1.  **Copy the content** of `gitlab_deploy_key` (the file *without* the extension).
    - It should start with `-----BEGIN OPENSSH PRIVATE KEY-----`.
2.  Go to your **GitLab Project**.
3.  Navigate to **Settings** > **CI/CD**.
4.  Expand **Variables**.
5.  Click **Add variable**:
    - **Key**: `SSH_PRIVATE_KEY`
    - **Value**: Paste the entire private key content.
    - **Type**: Variable (default).
    - **Protect variable**: Uncheck if you want it to run on non-protected branches, or keep checked if only deploying from `main`.
    - **Mask variable**: Uncheck (Private keys often cannot be masked due to characters).
6.  Click **Add variable**.

## 4. Add Other Variables
While you are in the GitLab Variables section, ensure you have these as well:

-   `SSH_HOST`: The public IP address or domain name of your Raspberry Pi.
-   `SSH_USER`: The username on the Pi (usually `pi`).
-   *(Optional)* `SSH_PORT`: `22` (You hardcoded this in the file, so this variable is not strictly needed anymore, but good practice).

## 5. Verify
The next time you push to the `main` branch, GitLab will:
1.  Run tests.
2.  Load the private key.
3.  SSH into your Pi using the address in `SSH_HOST`.
4.  Execute the `deploy.sh` script.

## Cleaning Up
Once configured, you can delete the `gitlab_deploy_key` and `gitlab_deploy_key.pub` files from your local machine, or store them securely in a password manager. **Do not commit them to the repository.**
