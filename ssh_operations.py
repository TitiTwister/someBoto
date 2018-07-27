import sys, paramiko

def ssh_commands(hostname, key, commands, username='centos', password='nope', port=22):
    
    commands = [ "ls /home/centos","ls /etc/salt"]
    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(hostname, username=username, password=password, key_filename=key)

    for command in commands:
            stdin, stdout, stderr = ssh.exec_command(command)
            print stdout.readlines()

    ssh.close()
