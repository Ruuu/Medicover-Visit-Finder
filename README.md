# Medicover-Visit-Finder
Simple script which allows user to automatically find visits/doctors in defined specializations.

Skrypt parsujący automatycznie serwis Medicover Online w celu wyszukania interesujących nas wizyt u lekarzy.

W pliku config.py należy zdefiniować nastepujące zmienne:
- ścieżka do programu phantomjs - http://phantomjs.org/
- ścieżka do programu Google Chrome - w przypadku chęci korzystania z trybu debug
- podmienić MEDICOVER_LOGIN_NR - login do panelu Medicover Online
- podmienić MEDICOVER_PASSWORD - hasło do panelu Medicover Online
- przynajmniej jeden element w słowniku 'visits', np:
{
 'type' : VISIT_TYPE.BADANIE_DIAGNOSTYCZNE,
 'specialization' : 'Testy',
 'time_intervals' : [ '-08:30', '15:00-16:00', '19:00-' ]
}
- dane dotyczące serwera smtp oraz wiadomości e-mail (opcjonalne; jeżeli zmienna 'send' == true)
