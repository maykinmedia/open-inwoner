.. _installation_index:

============
Installation
============

Open Inwoner can be installed and run in several ways:

1. Run with :ref:`Docker-Compose <installation_docker_compose>` on your
   computer -- as a full, self-contained stack for demoing or trying out OIP,
   or with Open Inwoner itself run on the host instead, for development and
   debugging against every other service for real. Both modes are covered in
   :ref:`installation_docker_compose`.
2. Run entirely from :ref:`Python code <installation_development>` on your
   computer, with no Docker at all -- for development environments that
   can't use Docker.
3. Deploy using :ref:`Ansible <installation_ansible>` for public testing and
   production purposes

.. toctree::
    :maxdepth: 1
    :caption: Further reading

    docker-compose
    development
    ansible
    celery
    health_checks
