import paramiko
import yaml
import json
import argparse
import logging
import os.path
import sys

def get_ssh_connection(ip, username, password):
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip,22,username,password)
    return ssh

def get_shh_connection_by_key(ip, username, key_path, phrase=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    if phrase:
        key = paramiko.RSAKey.from_private_key_file(key_path, password=phrase)
    else:
        key = paramiko.RSAKey.from_private_key_file(key_path)    
    ssh.connect(ip, username=username, pkey=key)
    return ssh

def upload_file(ssh, connectionInformation, uploadInformation):
    # First put to home directory
    status = sftp.put(uploadInformation['sourceFileFullPath'], '/home/' + connectionInformation['username'] + '/' + uploadInformation['destinyFileName'])
    # Second copy the file to destiny directory.
    # Command:[ -d "/etc/elasticsearch" ] && echo "directory exist." || (echo "directory not exist, create it." && sudo mkdir -p /etc/elasticsearch) && sudo cp /home/yhe/key.pem /etc/elasticsearch/key.pem
    stdin, stdout, stderr = ssh.exec_command('([ -d "' + uploadInformation['destinyDirectory'] + '" ] && echo "directory exist. copy file" || (echo "directory not exist, create it. copy file." && sudo mkdir -p ' + uploadInformation['destinyDirectory'] + ')) && sudo cp /home/'+connectionInformation['username']+'/' + uploadInformation['destinyFileName'] + ' ' + uploadInformation['destinyDirectory'] + '/'+  uploadInformation['destinyFileName'])
    for line in stdout:
        logger.info(line.strip('\n'))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser(description='Cluster management tool', allow_abbrev=True)
    parser.add_argument('-action', nargs='?', choices=['uploadFiles', 'runCommands'], help='Available choice uploadFiles|runCommand')
    parser.add_argument('-command', nargs='*', help='The commands will be excuted. This will overwrite the commands in configs.yml')
    args = parser.parse_args()
    #ssh = get_ssh_connection('52.187.13.120', 'yhe', '1qaz@WSX3edc')
    #ssh = get_shh_connection_by_key('13.94.24.168', 'prismadmin', os.path.join(os.path.dirname(__file__),'key.pem'), 'd2016H1-Prism')
    config_path = os.path.join(os.path.dirname(__file__), "configs.yml")
    with open(config_path, 'r') as config_path_f:
        configs = yaml.load(config_path_f)
    
    connectionSettings = configs['connectionSettings']
    for ip in connectionSettings['ips']:
        # Get connection
        if connectionSettings['method'] == 'password':
            ssh = get_ssh_connection(ip, connectionSettings['username'], connectionSettings['password'])
        elif connectionSettings['method'] == 'key':
            ssh = get_shh_connection_by_key(ip, connectionSettings['username'],connectionSettings['keyPath'], connectionSettings['keyPhrase'])
        # Run actions
        actionConfigs = configs['actions'][args.action]
        if args.action == 'uploadFiles':
            sftp = ssh.open_sftp()
            for uploadInfo in actionConfigs:
                upload_file(ssh, connectionSettings, uploadInfo)
                    
        elif args.action == 'runCommands':
            if args.command != None:
                commands = args.command
            else:
                commands = actionConfigs
            for command in commands:
                stdin, stdout, stderr = ssh.exec_command(command)
                for line in stdout:
                    logger.info(line.strip('\n'))
        ssh.close()