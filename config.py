# -*- coding: utf-8 -*-

class VISIT_TYPE( object ):
    KONSULTACJA = "Konsultacja"
    BADANIE_DIAGNOSTYCZNE = "Badanie diagnostyczne"

SETTINGS = {
                'phantomjs' : 'C:/Users/Piotr/Programy/phantomjs-2.0.0-windows/bin/phantomjs.exe',
                'chrome' : 'C:/Users/Piotr/Programy/chromedriver.exe'
            }

USERS = {
          'MEDICOVER_LOGIN_NR' : {  # LOGIN
                       'pass' : 'MEDICOVER_PASSWORD',  # PASSWORD
                       'city' : 'Warszawa',
                       'visits' : [
                                  {
                                   'type' : VISIT_TYPE.BADANIE_DIAGNOSTYCZNE,
                                   'specialization' : 'Testy',
                                   'time_intervals' : [ '11:10-', '-08:00' ]
                                  },
                                  {
                                   'type' : VISIT_TYPE.KONSULTACJA,
                                   'specialization' : 'Cytologia',
                                   'time_intervals' : [ '-09:00', '11:10-15:30', '18:00-' ]
                                  }
                                ],
                       'mail' : {
                                 'send' : True,

                                 'smtp' : 'SMTP_SERVER_NAME',
                                 'port' : 465,
                                 'ssl' : True,
                                 'login' : 'EMAIL_LOGIN',
                                 'pass' : 'EMAIL_PASS',
                                 'from' : 'EMAIL_FROM',
                                 'to' : 'EMAIL_TO'
                                }
                    }
          }

if __name__ == '__main__':
    from pprint import pprint
    pprint( USERS )
