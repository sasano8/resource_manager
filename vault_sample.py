import hvac


def get_client():
    client = hvac.Client(
        url="http://127.0.0.1:8200",
        token="vault-token",
    )
    return client


def main(client: hvac.Client):
    """
    https://python-hvac.org/en/stable/usage/secrets_engines/kv_v2.html
    """
    PATH = "my-secret-password"
    MOUNTPOINT = ""

    try:
        # パスが作成されていないとエラーが生じる
        list_response = client.secrets.kv.v2.list_secrets(
            path=PATH,
        )
        for key in list_response["data"]["keys"]:
            print(key)
    except Exception as e:
        ...

    res = client.secrets.kv.v2.create_or_update_secret(
        path=PATH,
        secret=dict(password="Hashi123"),
    )
    print(res)

    res = client.secrets.kv.v2.read_secret_version(
        path=PATH, raise_on_deleted_version=False
    )
    print(res)
    # print(res['data']['data']['password'])

    res = client.secrets.kv.v2.patch(
        path=PATH,
        secret=dict(password="Hashi456"),
    )
    print(res)

    # 削除が成功すると 204 レスポンスを返す
    # res = client.secrets.kv.v2.delete_metadata_and_all_versions(
    #     path=PATH,
    # )
    # print(res)

    # latest の指定方法がよくわからない
    res = client.secrets.kv.v2.delete_secret_versions(
        path=PATH,
        versions=[1, 2, 3],
    )
    print(res)


main(get_client())
