# Deploying

This document explains how to deploy a project. If you want to add deployment
scripts to a new project, check out `INSTALL.md`.

## Prerequisites

You need:

* Access to the server.
* Ansible installed globally or locally.

## Deploying this project

From the project root folder, do:

    $ cd deployment
    $ git submodule update --init  # First time only
    $ ansible-galaxy install -r requirements.yml

Then deploy your project using one of the following:

    $ ansible-playbook test.yml
    
    $ ansible-playbook staging.yml
    
    # ansible-playbook production.yml
    
### Deploy via a jump host or bastion server

If you are in a location that is not white-listed, you can use a jump host
as a tunnel. We use `rachel.maykinmedia.nl` for this.

1. In the `maykin-deployment` folder, add this to the top the `hosts` file:

        [gatewayed]
        # Example: sansa.maykinmedia.nl ansible_host=5.79.106.49
        <target hostname> ansible_host=<target host ip>

2. Create a file `group_vars/gatewayed.yml` with the following contents:

        ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q <username>@rachel.maykinmedia.nl"'

3. Now you can run Ansible with:

        ansible-playbook <playbook> --limit gatewayed

## Updating the generic deployment files

To get the latest changes for generic deployment files (like firewall policies,
backup routines, etc.), do:

    $ git submodule foreach git pull origin master
    $ git commit ./deployment/maykin-deployment -m "Updated maykin-deployment submodule"
