<?xml version="1.0" encoding="utf-16"?>

<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	  xmlns:msxsl="urn:schemas-microsoft-com:xslt"            
	>

  <xsl:output method="xml" version="1.0" encoding="utf-8" omit-xml-declaration="no" indent="yes"/>
   
  <xsl:template match="Uitkeringsspecificatie">

    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
                       xmlns:gwsb="http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600" 
                       xmlns:gwsh="http://www.centric.nl/GWS/Header/v0201" 
                       xmlns:wsa="http://www.w3.org/2005/08/addressing">
        <SOAP-ENV:Header>
          <wsa:MessageID>
            <xsl:value-of select="MessageId"/>
          </wsa:MessageID>
          <wsa:Action>
            <xsl:value-of select="SoapAction"/>
          </wsa:Action>
          <gwsh:Header>
            <RouteInformatie>
              <Bron>
                <Bedrijfsnaam>
                  <xsl:value-of select="Bedrijfsnaam"/>
                </Bedrijfsnaam>
                <ApplicatieNaam>
                  <xsl:value-of select="Applicatienaam"/>
                </ApplicatieNaam>
              </Bron>
              <Bestemming>
                <Gemeentecode>
                  <xsl:value-of select="Gemeentecode"/>
                </Gemeentecode>
              </Bestemming>
            </RouteInformatie>
            <BerichtIdentificatie>
              <DatTijdAanmaakRequest>
                <xsl:value-of  select="Aanmaakdatum"/>
              </DatTijdAanmaakRequest>
              <DatTijdOntvangstRequest>
                <xsl:value-of  select="Aanmaakdatum"/>
              </DatTijdOntvangstRequest>
              <DatTijdAanmaakResponse>2012-09-12T15:01:47+01:00</DatTijdAanmaakResponse>
              <DatTijdOntvangstResponse>2012-09-12T15:01:47+01:00</DatTijdOntvangstResponse>
              <ApplicatieInformatie>
                <xsl:value-of  select="ApplicatieInformatie"/>
              </ApplicatieInformatie>
            </BerichtIdentificatie>
          </gwsh:Header>
        </SOAP-ENV:Header>
        <SOAP-ENV:Body>
          <gwsb:Request>
            <BurgerServiceNr>
              <xsl:value-of select="BSN"/>
            </BurgerServiceNr>
            <Periodenummer>
              <xsl:value-of select="Periode"/>
            </Periodenummer>
          </gwsb:Request>
        </SOAP-ENV:Body>
      </SOAP-ENV:Envelope>

  </xsl:template>

</xsl:stylesheet>
