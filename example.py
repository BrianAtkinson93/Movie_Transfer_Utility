import argparse
import glob
import os
import sys

from tqdm import tqdm

import paramiko


def progress_bar_callback(transferred, total):
    progress_bar.update(transferred - progress_bar.n)


def ensure_remote_path(sftp, remote_path, check_for, sub_dir) -> None:
    """
    Ensure the remote directory exists, create it if it doesn't.
    """
    if check_for not in sftp.listdir(f'/opt/plexmedia/{sub_dir}/'):
        print(f'Creating location: {remote_path} ...')
        sftp.mkdir(remote_path)
        print(f'    Created...')


def transfer_file(content_type, local_path, remote_path, file_name, hostname, port, username, key_file) -> None:
    print('*' * 50)
    print(f'{file_name} ...')
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.RSAKey.from_private_key_file(key_file)
        ssh.connect(hostname, port=port, username=username, pkey=private_key)
        print("    Connected to the server")

        sftp = ssh.open_sftp()

        check_for = remote_path.split(f'{content_type}/')[-1]
        ensure_remote_path(sftp, remote_path, check_for, content_type)

        # Initialize the progress bar
        file_size = os.path.getsize(local_path)

        # Recreate the final path to file
        remote_loc = remote_path + os.sep + file_name

        if file_name in sftp.listdir(remote_path + os.sep):
            print(f'        File already exists...', file=sys.stderr)
            print(f'        Continuing ...', file=sys.stderr)
            return None

        global progress_bar
        progress_bar = tqdm(total=file_size, unit='B', unit_scale=True,
                            desc=f"Transferring {os.path.basename(local_path)}")

        # Transfer the file with the progress bar callback
        sftp.put(local_path, remote_loc, callback=progress_bar_callback)
        progress_bar.close()

        print(f"    Successfully transferred {local_path} to {remote_path}")

        sftp.close()
        ssh.close()

    except Exception as e:
        print(f"Failed to transfer file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Transfer files to a remote server.")

    # Required arguments
    required = parser.add_argument_group('Required')
    required.add_argument('files_to_transfer', type=str, help="File or pattern to transfer")

    # General Arguments
    general = parser.add_argument_group('General')
    general.add_argument('--pattern', action='store_true', default=False, help="Set this flag if using a file pattern")
    general.add_argument("--movie", default=False, action="store_true",
                        help="If the transfers is/are movie(s), please set the --movie flag.")
    general.add_argument('--series', default=False, action='store_true',
                        help='If the transfers is/are series, Please set the --series flag.')

    # Advanced configuration
    advanced = parser.add_argument_group('Advanced')
    # TODO Change path to default location ( Requires changes on line 19 )
    advanced.add_argument('--remote_location', type=str, default='/opt/plexmedia/',
                        help="Remote location to store the files")
    # TODO Change ip address
    advanced.add_argument('--hostname', type=str, default='192.168.1.1',
                        help="Hostname or IP address of the remote server")
    # TODO Change username
    advanced.add_argument('--username', type=str, default='user', help='Username for SSH authentication')
    # TODO Change default port if required
    advanced.add_argument('--port', type=int, default=22, help="SSH port of the remote server")
    # TODO Change default path to ssh key
    advanced.add_argument('--key_file', type=str, default='/Path/to/.ssh/name',
                        help="Path to the SSH private key file")

    args = parser.parse_args()

    if not args.series and not args.movie:
        print(f'You must select a type for transfer, is the transfer of type --series or --movie ?', file=sys.stderr)
        sys.exit(1)

    content_type = "movies" if args.movie else "series"

    # Handle file patterns
    if args.pattern:
        files = sorted(glob.glob(args.files_to_transfer))
    else:
        files = sorted([args.files_to_transfer])

    print(f'Moving files...')
    [print(f"   {i}: {file}") for i, file in enumerate(files)]

    for file in files:
        local_file_path = file
        file_name = os.path.basename(local_file_path).replace(" ", "_")
        transfer_file(content_type, local_file_path, args.remote_location, file_name, args.hostname, args.port, args.username,
                      args.key_file)


if __name__ == "__main__":
    main()
