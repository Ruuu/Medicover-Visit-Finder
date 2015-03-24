# -*- coding: utf-8 -*-

import datetime
from email.MIMEMultipart import MIMEMultipart
from email.mime.text import MIMEText
import hashlib
import optparse
import os
import pickle
import pprint
import re
import smtplib
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from config import SETTINGS
from config import USERS
from config import VISIT_TYPE


class Medicover( object ):
    # Phantomjs executable file path
    PHANTOMJS = SETTINGS[ 'phantomjs' ]
    # Chrome executable file path
    CHROME = SETTINGS[ 'chrome' ]
    # Database name postfix and extension
    DB_NAME = "db.pickle"

    def __init__( self, users, debug = False ):
        self._users = users
        self.DEBUG = debug
        if self.DEBUG is True:
            self._driver = webdriver.Chrome( self.CHROME )
        else:
            if not os.path.exists( self.PHANTOMJS ):
                raise Exception( "Phantomjs executable file not found" )
            self._driver = webdriver.PhantomJS( self.PHANTOMJS )

        self._wait = WebDriverWait( self._driver, 10 )

    def run( self ):
        print 'Run medicover doctor auto-finder'
        # For every user from config file
        for userLogin, userData in self._users.iteritems():
            # Load DB
            self.loadDB( userLogin )
            # Login user
            self.login( userLogin, userData[ 'pass' ] )
            # Check all visits
            self.checkVisits( userData )
            # Send email
            self.sendEmail( userData )
            # Save DB
            self.saveDB( userLogin )

    def loadDB( self, userLogin ):
        dbName = userLogin + "_" + self.DB_NAME
        if os.path.exists( dbName ):
            print "Loading databse:", dbName
            self._db = pickle.load( open( dbName, "r" ) )
        else:
            print "Creating databse"
            self._db = {}

    def saveDB( self, userLogin ):
        dbName = userLogin + "_" + self.DB_NAME
        print "Saving databse:", dbName
        pickle.dump( self._db, open( dbName, "w" ) )

    def login( self, userLogin, userPass ):
        print 'Login user:', userLogin
        # Get login page
        self._driver.get( 'http://mol.medicover.pl' )
        # Get inputs
        loginInput = self._driver.find_element_by_xpath( '//input[ @id="username-email" ]' )
        passInput = self._driver.find_element_by_xpath( '//input[ @id="password" ]' )

        # Fill login form
        loginInput.send_keys( userLogin )
        passInput.send_keys( userPass )

        # Login
        passInput.send_keys( Keys.RETURN )

        print 'User', userLogin, 'logged'

        return True

    def _waitForSearchFormAndClick( self ):
        try:
            self._wait.until( lambda driver: driver.find_element_by_id( 'advancedSearchForm' ) )
            # Expand search form
            self._driver.find_element_by_xpath( '//div[ @id="advancedSearchForm" ]//div[ contains( @class, "row" ) ]//a' ).click()
        except WebDriverException as e:
            time.sleep( 3 )
            print "Trying to expand search form again..."
            self._waitForSearchFormAndClick()

    def _findOption( self, select, optionToFind ):
        print "Looking for '", optionToFind, "' in", [ o.text for o in select.options ]
        for option in select.options:
            if re.findall( optionToFind, option.text ):
                select.select_by_value( option.get_attribute( 'value' ) )
                return True
        return False

    def checkVisits( self, userData ):
        # Get 'my visits' page
        self._driver.get( 'https://mol.medicover.pl/MyVisits' )
        # self._driver.find_element_by_partial_link_text( u'Umów wizytę' ).click()
        # Wait for search form
        self._waitForSearchFormAndClick()

        # Select city
        try:
            Select( self._driver.find_element_by_id( 'RegionId' ) ).select_by_visible_text( userData[ 'city' ] )
        except NoSuchElementException as e:
            raise Exception( 'City not found: ' + str( userData[ 'city' ] ) )

        time.sleep( 3 )

        # Loop over all defined visits
        for visit in userData[ 'visits' ]:
            print "Check visit:"
            pprint.pprint( visit )

            # Select visit type
            visitTypes = Select( self._driver.find_element_by_id( 'BookingTypeId' ) )
            if not self._findOption( visitTypes, visit[ 'type' ] ):
                raise Exception( 'Visit type not found: ' + str( visit[ 'type' ] ) )

            time.sleep( 3 )

            # Select specialization
            if visit[ 'type' ] == VISIT_TYPE.KONSULTACJA:
                specializations = Select( self._driver.find_element_by_id( 'SpecializationId' ) )
            elif visit[ 'type' ] == VISIT_TYPE.BADANIE_DIAGNOSTYCZNE:
                specializations = Select( self._driver.find_element_by_id( 'ServiceId' ) )
            if not self._findOption( specializations, visit[ 'specialization' ] ):
                raise Exception( 'Specialization not found: ' + str( visit[ 'specialization' ] ) )

            time.sleep( 3 )

            # Click search
            # self._driver.find_element_by_xpath( '//div[ @class="search-button" ]/button' ).click() # NOT VISIBLE
            for _ in range( 3 ):
                self._driver.find_element_by_xpath( '//div[ contains( @class, "input-group" ) and contains( @class, "date" ) and contains( @class, "date-picker" ) ]/input' ).send_keys( Keys.RETURN )
                time.sleep( 0.5 )

            time.sleep( 3 )

            # Load more
            for _ in range( 10 ):
                try:
                    self._wait.until( expected_conditions.presence_of_element_located( ( By.CSS_SELECTOR, '.btn.default.col-lg-4' ) ) )
                    self._driver.find_element_by_css_selector( '.btn.default.col-lg-4' ).click()
                except ( NoSuchElementException, WebDriverException ):
                    break

            time.sleep( 3 )

            # Read all terms
            terms = self._driver.find_elements_by_xpath( '//div[ contains( @class, "freeSlot-box") ]' )
            for term in terms:
                d = term.find_element_by_xpath( './div[ contains( @class, "freeSlot-head" ) ]/span' ).text
                t = term.find_element_by_xpath( './div[ contains( @class, "freeSlot-head" ) ]/span[ contains( @class, "pull-right" ) ]' ).text
                c = term.find_element_by_xpath( './div[ contains( @class, "freeSlot-content" ) ]/p[ contains( @class, "clinicName" ) ]' ).text

                print d, t, c

                tObj = self._createTime( t )

                timeConditionAccept = False
                if len( visit[ 'time_intervals' ] ) == 0:
                    timeConditionAccept = True
                for timeInterval in visit[ 'time_intervals' ]:
                    timeIntervalArr = timeInterval.split( '-' )
                    if len( timeIntervalArr ) != 2:
                        print "Wrong time interval:", timeInterval
                        continue
                    timeFromObj = self._createTime( timeIntervalArr[ 0 ] )
                    timeToObj = self._createTime( timeIntervalArr[ 1 ] )

                    # Time conditions
                    if ( timeFromObj and tObj >= timeFromObj ) or ( timeToObj and tObj <= timeToObj ):
                        timeConditionAccept = True
                        break

                if timeConditionAccept is True:
                    print "\tOK"
                    result = {}
                    result[ 'visit_type' ] = visit[ 'type' ]
                    result[ 'specialization' ] = visit[ 'specialization' ]
                    result[ 'email' ] = False
                    result[ 'date' ] = d
                    result[ 'time' ] = t
                    result[ 'clinic' ] = c

                    digest = self._getDigest( pprint.pformat( result ) )

                    if not self._db.has_key( digest ):
                        print "\tAdd to database:", digest
                        self._db[ digest ] = result
                    else:
                        print d, t, c, "is already in database"

        # Close browser
        self._driver.close()

        return

    def sendEmail( self, userData ):
        if userData[ 'mail' ][ 'send' ] is False:
            return
        print "Sending email to:", userData[ 'mail' ][ 'to' ]
        msg = ""

        for digest, result in self._db.iteritems():
            if result[ 'email' ] is False:
                print "Add to email:", digest
                result[ 'email' ] = True
                msg += " - ".join( [ result[ 'visit_type' ], result[ 'specialization' ], result[ 'date' ], result[ 'time' ], result[ 'clinic' ] ] )
                msg += "\n"

        connect = smtplib.SMTP
        if userData[ 'mail' ][ 'ssl' ] is True:
            connect = smtplib.SMTP_SSL
        s = connect( userData[ 'mail' ][ 'smtp' ], userData[ 'mail' ][ 'port' ] )  # (235, 'go ahead')
        s.login( userData[ 'mail' ][ 'login' ], userData[ 'mail' ][ 'pass' ] )
        s.ehlo()

        msgToSend = MIMEMultipart()
        msgToSend[ 'Subject' ] = 'Medicover doctor finder: ' + str( datetime.datetime.now() )
        msgToSend[ 'From' ] = userData[ 'mail' ][ 'from' ]
        msgToSend[ 'To' ] = userData[ 'mail' ][ 'to' ]
        msgToSend.attach( MIMEText( msg.encode( 'utf-8' ) ) )

        s.sendmail( userData[ 'mail' ][ 'from' ], userData[ 'mail' ][ 'to' ], msgToSend.as_string() )
        s.quit()  # (221, 'smtp.wp.pl')
        print "Email sent to:", userData[ 'mail' ][ 'to' ]

    def _createTime( self, s ):
        if len( s.strip() ) > 0:
            return datetime.datetime.strptime( s, "%H:%M" )
        else:
            return None

    def _getDigest( self, s ):
        md5 = hashlib.md5()
        md5.update( s )
        return md5.hexdigest()

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option( '-d', '--debug',
                      dest = "debug",
                      default = False,
                      action = "store_true",
                      )
    options, remainder = parser.parse_args()

    print 'DEBUG:', options.debug

    medicover = Medicover( USERS, options.debug )
    medicover.run()
