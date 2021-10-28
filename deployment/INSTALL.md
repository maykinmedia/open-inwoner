# Installation

This document describes how to use this `example-deployment` for a new project.

The `example-deployment` takes care of most tasks for provisioning a server
from scratch and results in a working application that is secure, monitored and
backed up to a remote location.

## Prerequisites

You need:

* A (new) project that's versioned with Git.
* Hostname of the server where the project will run, for example: 
  `arya.maykinmedia.nl`.
* Access to the server.
* Ansible installed globally or locally.

While the hostname is `arya.maykinmedia.nl` we call the first part (before the
first dot), the "short hostname": `arya`.

## Preparations

Some variables are stored within the `maykin-deployment` folder to make tasks
over several servers easier.

Update the `maykin-deployment` repository.

1. Add the server hostname in the project root `hosts` file and (optionally)
   add it to a group (indicated with `:children`):

        # <Project name>
        [<short hostname>]
        <hostname>

   For example:

        # Aethon

        [arya] # Production server
        arya.maykinmedia.nl

        [sansa]  # Staging server
        sansa.maykinmedia.nl

        [aethon:children]
        arya
        sansa

2. Generate a sudo password and its hash, for the `maykin` user:

        $ < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${1:-32};echo;
        ltSfprgDSZAyd-snTVULZxeKODWsk-ON

        $ mkpasswd --method=SHA-512
        Password: <copy/paste the generated password above>
        $6$MtF1EZf9cWqfWU$aLkmoqTie9BlTCu48StTxi7p5o7VHqAMiYgjhOjG0vfnAqyOJxI2fzx9Ym3vvWgfOsglw8NJ9FwuVf2Yawrn71

3. Create a secrets file using Ansible vault:

        $ mkdir group_vars/<short hostname>
        $ ansible-vault create group_vars/<short hostname>/sudo_vars.yml

4. Add the following two entries as secrets:

        ansible_sudo_pass: <password>
        hashed_sudo_pass: <password hash>

5. Commit and push all changes:

        $ git commit -a -m "Added new server"
        $ git push
 
## Setting up project deployment

We're using the generic `maykin-deployment` and the `example-deployment` within
that repository to add a deployment script specific for this project.

1. Create a project `deployment` folder:

        $ mkdir deployment
        $ cd deployment

2. Add `maykin-deployment` as submodule to your project:

        $ git submodule add git@bitbucket.org:maykinmedia/maykin-deployment.git ./deployment/maykin-deployment
        $ git submodule update --init
        $ git commit ./maykin-deployment -m "Added maykin-deployment submodule"

   This should also contain the intended server for this project, as done under
   the preparations section.

3. Copy the example files to your project:

        $ cp -R maykin-deployment/example-deployment/ .

4. Change files where needed but take special note of the `vars/*.yml` files 
   and the `host` parameter in the `*.yml` files.

5. Add everything to git:

        $ git add --all
        $ git commit -m "Added initial deployment"

## Backup configuration

Allow backups to be created. Note that this can only be done by a project 
manager.

1. Create a key-pair on the server:

        $ ssh maykin@<hostname>
        
        [user@<hostname>]$ su
        [root@<hostname>]$ ssh-keygen
        [root@<hostname>]$ cat .ssh/id_rsa.pub

2. Create an account on the backup server:

        $ ssh <user>@backup.maykinmedia.nl
        
        [<user>@backup]$ su
        [root@backup]$ adduser <short hostname> --disabled-password
        [root@backup]$ su <short hostname>
        [<short hostname>@backup]$ cd ~
        [<short hostname>@backup]$ mkdir ~/.ssh
        [<short hostname>@backup]$ nano .ssh/authorized_keys  # Paste public key here and save.
        [<short hostname>@backup]$ chmod 600 ~/.ssh/authorized_keys
        [<short hostname>@backup]$ mkdir backup

3. Verify that the `root` user can connect to the backup server:

        [root@<hostname>]$ ssh <short hostname>@backup.maykinmedia.nl

## Initial deploy

Running the Ansible playbook for the first time as `root`:

    $ ansible-playbook <test|staging|production>.yml --limit opengem.maykin.test --user root --ask-pass

### Repeated deploys

After the initial run, we can no longer login as `root` over SSH. Running the 
Ansible playbook later on, requires the `maykin` user (which is the default):

    $ ansible-playbook <test|staging|production>.yml

## Troubleshooting

 **Ansible does not connect to the server**
 
 Ensure you have logged into the server to accept the server's SSH host key.

 **Ansible complains about Python**
 
 Make sure Python is installed on the server, run: `apt-get update` and 
 `apt-get install python`.

 **Server hostname is incorrect**
 
 Configure the hostname in `/etc/hostname` and `/etc/hosts` on the server.

 **Locale issues**
 
 Certain images don't have the correct locales pre-installed, run:
 `dpkg-reconfigure locales`

**Ansible cannot sudo**

 Certain images don't have a Debian-generated `/etc/sudoers` file or its 
 overwritten. Ensure it has the following, to allow members of the group `sudo`
 to do `sudo`:

    Defaults	env_reset
    Defaults	secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    %sudo	ALL=(ALL:ALL) ALL

**Executing from the tmp folder**

If you have the error that you can not execute files that are stored in the 
`/tmp/` folder. Add this before you install your python dependencies:

    os.environ['TMPDIR'] = '/var/tmp/'
    call(os.path.join(virtualenv, 'bin', 'pip') + ' install -r requirements/%s.txt' % args.target, shell=True)
