O programie:
VCJB jest prostym botem, który sprawdza w systemie kontroli wersji,
czy nie pojawi³y siê nowe wersje. Po pojawieniu siê nowej wersji wysy³a 
przez jabbera wiadmo¶æ.
Aktualnie VCJB obs³uguje jedynie repozytoria SVN, ale ka¿dy mo¿e stworzyæ
plugin dla innych systemów kontroli wersji.
Plugin PUB wraz z klas± publishApplication obs³uguje informacje
nades³ane do VCJB po zatwierdzeniu zmian w repozytorium. Mo¿e on byæ 
wykorzystany do obs³ugi dowolnego systemu kontroli wersji.
Np. w repozytorium CVS wystarczy odpowiednio zmodyfikowaæ plik publish.py 
i uruchomiæ go w skrypcie CVSROOT/loginfo.
W przysz³o¶ci klasa publishApplication bêdzie obs³ugiwa³a mechanizm 
Publish-Subscribe (http://www.jabber.org/jeps/jep-0060.html).

Wymagania:
Python 2.3 (http://www.python.org)
PyXMPP  (http://pyxmpp.jabberstudio.org)

Instalacja: 
* Za³ó¿ na serwerze jabbera konto dla vcjb
* Utwórz w³asny plik konfiguracyjny vcjb.cfg
* Uruchom program: python vcjb.py

Wszystkie dostêpne komendy administracyjne wypisane s± w pliku COMMANDS.

Kontakt:
JID: pete@chrome.pl
email: petecky@users.berlios.de
