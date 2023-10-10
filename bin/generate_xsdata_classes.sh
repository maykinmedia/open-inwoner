#!/bin/bash

rm -rf ./src/open_inwoner/ssd/service
cd ./src

xsdata --package open_inwoner.ssd.service.jaaropgave "open_inwoner/ssd/files/jaaropgave/v0400-b01/JaarOpgaveClient.wsdl"
xsdata --package open_inwoner.ssd.service.uitkering "open_inwoner/ssd/files/uitkering/v0600-b01/UitkeringsSpecificatieClient.wsdl"
