#!/bin/sh
ansible-playbook -i hosts -v -b keepup-postgres.yml
ansible-playbook -i hosts -v -b keepup.yml