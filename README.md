# MIA (Medical Information Assistant)
A virtual HIPAA-compliant clinical consentbot that facilitates virtual conversations with patients.

MIA is designed to be deployed in a variaty of environments. If configurd properly it should work with any external application that presents properly formatted API requests with appropirate authentication credentials.

This repository is composed of two serivce applications. The server application is a Django API DB and the client application is a Redux/React UI.

## Deployment

- [Local deployment](docs/deployment/localDeployment.md) 
    - For develpment or internal use only
- [Production deployment](docs/deployment/productionDeployment.md)
    - For deployment that is exposed to the internet
- [Docker deployment](docs/deployment/dockerDeployment.md)
    - WIP: comming soon

## Development and troubleshooting
- [Contribution Guide lines](docs/CONTRIBUTING.md)
- [FAQ and trouble shooting](docs/faq.md)
- [`.secretes` configuration](docs/config.md)
- [Testing](docs/testing.md)
