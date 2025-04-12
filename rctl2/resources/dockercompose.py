import subprocess


class DockerComposeSericeManager:
    @classmethod
    def create(cls, service_name):
        return cls(service_name=service_name)

    def __init__(self, service_name):
        self._service_name = service_name

    def exists(self):
        result = subprocess.run(
            ["docker", "compose", "ps", self._service_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )

        if result.returncode:
            return False

        # docker compose にサービスが定義されていると、常に returncode == 0 が返る
        # Up されているか確認する
        for line in result.stdout.splitlines():
            if self._service_name in line and "Up" in line:
                return True

        return False

    def up(self, sleep: int = 1):
        if not self.exists():
            import subprocess
            import time

            result = subprocess.run(
                ["docker", "compose", "up", "-d", self._service_name]
            )
            time.sleep(sleep)
            return not result.returncode

    def down(self):
        import subprocess

        result = subprocess.run(["docker", "compose", "down", self._service_name])
        return not result.returncode
