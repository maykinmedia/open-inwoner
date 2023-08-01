# Certificates for testing purposes

`test.crt` and `test.key` were created with the following command:

openssl req -x509 \
            -newkey rsa:4096 \
            -sha256 \
            -days 356 \
            -nodes \
            -subj "/CN=maykin.test/C=NL/L=Amsterdam" \
            -keyout test.key -out test.crt

Tests using these files will fail when the certificates have expired.
