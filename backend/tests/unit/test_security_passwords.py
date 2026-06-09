from app.common.security import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "s3cur3-p@ssw0rd"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_hash_is_stable_format(self):
        hashed = hash_password("test")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
