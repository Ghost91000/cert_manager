from cryptography import x509
from cryptography.hazmat._oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes


async def get_subject(file):
    cert_data = await file.read()
    try:
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    except ValueError:
        cert = x509.load_der_x509_certificate(cert_data, default_backend())
    #print(cert.fingerprint(hashes.SHA1()).hex())
    return {"issuer": cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
            "subject": cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
            "version": cert.version.value + 1,
            "thumbprint": cert.fingerprint(hashes.SHA1()).hex(),
            "date_to": cert.not_valid_after_utc.date(),
            "date_from": cert.not_valid_before_utc.date()}
