# module for ssh operations
from pexpect import spawn
from pexpect.exceptions import EOF, TIMEOUT

from exceptions import ExecuteCommandFail, FileCopyFail, LoginFail, SetPasswordFail


class SSH:
    ssh_cmd = "ssh -p {port} -oStrictHostKeyChecking=no {username}@{host}"
    scp_cmd = "scp -P {port} -oStrictHostKeyChecking=no {static_file} {username}@{host}:{to_dir}"
    shell_prompt = "[#\$] "
    password_prompt = ".*[Pp]assword:"

    def __init__(
        self, host, username="root", password="7890", port=22, timeout=5
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self._client = None

    def login(self):
        try:
            _cmd = self.ssh_cmd.format(
                port=self.port, username=self.username, host=self.host
            )
            self._client = spawn(_cmd, timeout=self.timeout)
            self._client.expect(self.password_prompt)
            self._client.sendline(self.password)
            self._client.expect(self.shell_prompt)
        except TIMEOUT:
            raise LoginFail("Fail to login device and timeout occurs.")

    def close(self):
        self._client.close()

    def __enter__(self):
        if not self._client:
            self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._client.closed:
            self.close()

    def execute(self, cmd: str):
        try:
            self._client.sendline(cmd)
            self._client.expect(self.shell_prompt)
            output = self._client.before.decode()
        except TIMEOUT:
            raise ExecuteCommandFail("Fail to execute command and timeout occurs.")
        except EOF:
            raise ExecuteCommandFail("Fail to execute command and EOF occurs.")
        return output

    def filecopy_to_device(self, local_file: str, to_remote_dir: str, timeout=5):
        try:
            _cmd = self.scp_cmd.format(
                port=self.port,
                static_file=local_file,
                username=self.username,
                host=self.host,
                to_dir=to_remote_dir,
            )
            _scp_client = spawn(_cmd, timeout=timeout)
            _scp_client.expect(self.password_prompt)
            _scp_client.sendline(self.password)
            _scp_client.expect(EOF)
            _scp_client.close()
        except TIMEOUT:
            raise FileCopyFail("Fail to copy file and timeout occurs.")
        except EOF:
            raise FileCopyFail("Fail to copy file and EOF occurs.")

    def set_new_password(self, new_password: str):
        try:
            self._client.sendline("passwd")
            for _ in range(3):
                res = self._client.expect([self.password_prompt, self.shell_prompt])
                if res == 0:
                    self._client.sendline(new_password)
                else:
                    break
        except TIMEOUT:
            raise SetPasswordFail("Fail to set new password and timeout occurs.")
        except EOF:
            raise SetPasswordFail("Fail to set new password and EOF occurs.")
