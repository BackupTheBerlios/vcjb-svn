O programie:
VCJB jest prostym botem, kt�ry sprawdza w systemie kontroli wersji,
czy nie pojawi�y si� nowe wersje. Po pojawieniu si� nowej wersji wysy�a 
przez jabbera wiadmo��.
Aktualnie VCJB obs�uguje jedynie repozytoria SVN, ale ka�dy mo�e stworzy�
plugin dla innych system�w kontroli wersji.
Plugin PUB wraz z klas� publishApplication obs�uguje informacje
nades�ane do VCJB po zatwierdzeniu zmian w repozytorium. Mo�e on by� 
wykorzystany do obs�ugi dowolnego systemu kontroli wersji.
Np. w repozytorium CVS wystarczy odpowiednio zmodyfikowa� plik publish.py 
i uruchomi� go w skrypcie CVSROOT/loginfo.
W przysz�o�ci klasa publishApplication b�dzie obs�ugiwa�a mechanizm 
Publish-Subscribe (http://www.jabber.org/jeps/jep-0060.html).

Wymagania:
Python 2.3 (http://www.python.org)
PyXMPP  (http://pyxmpp.jabberstudio.org)

Instalacja: 
* Za�� na serwerze jabbera konto dla vcjb
* Utw�rz w�asny plik konfiguracyjny vcjb.cfg
* Uruchom program: python vcjb.py

Wszystkie dost�pne komendy administracyjne wypisane s� w pliku COMMANDS.

Kontakt:
JID: pete@chrome.pl
email: petecky@users.berlios.de
