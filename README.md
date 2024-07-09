Zadatak (20 bodova)
Implementirati paralelni sistem za skladištenje fajlova. Sistem skladišti fajlove tako što ih deli na delove određene veličine, te kompresuje i čuva svaki deo posebno.

Komponente sistema
Registar fajlova
Registar fajlova je kolekcija koja sadrži spisak imena svih fajlova koji se čuvaju u sistemu, njihovih jedinstvenih identifikatora, kao i njihov status (da li je fajl spreman za upotrebu ili nije). Opciono, u registru se mogu čuvati dodatni podaci o fajlovima (npr. broj delova).

Registar delova fajlova
Registar fajlova je kolekcija koja sadrži spisak svih delova svih fajlova koji su dodati u sistem. U ovom registru se nalaze jedinstveni identifikatori delova, jedinstveni identifikatori fajlova kojima pripadaju, redni broj dela u fajlu iz kojega dolazi i MD5 heš sadržaja. Opciono, u registru se mogu čuvati dodatni podaci. Uz registar delova može postojati i indeks koji ubrzava pronalaženje svih delova koji pripaduju nekom fajlu (ovo je opciono).

Nit za prihvatanje komandi (2 boda)
Glavna nit u glavnom procesu služi isključivo za prihvatanje komandi sa komandne linije. Za svaku primljenu komandu pokreće se posebna nit koja tu komandu obrađuje (osim za komandu za gašenje).

Moguće komande su:

put
get
delete
list
exit
Niti za obradu komandi
Nit koja se spawnuje kada stigne komanda
Procesi za Ulaz / Izlaz (U/I procesi)
Komande
put (5 bodova)
Nit za obradu komande
Dodeljuje jedinstveni ID fajlu koji se dodaje
Dodaje fajl u registar fajlova
Čita fajl deo po deo:
Svakom delu dodeljuje jedinstveni identifikator
Dodaje deo u registar delova
Delove fajlova (pojedinačno ili u grupi) prosleđuje U/I procesima
Za svaki deo koji je prosleđen U/I procesima kao povratnu informaciju očekuje MD5 heš fajla; Kada ovaj podatak stigne, dodaje ga u registar delova i označava da je deo spreman.
Kada dobije potvrdu da je poslednji deo nekog fajla spreman, u registru fajlova označava ceo fajl kao spreman.
U/I procesi obrađuju deo fajla tako što:

Računaju md5 za taj deo
Kompresuju podatke
Ispisuju kompresovane podatke
Vraćaju MD5 (možda i neke dodatne podatke)
Napomene:
Fajl sa istim imenom može biti dodat više puta! Očekuje se da svaki put bude unet sa drugim identifikatorom.
Ukoliko se neki fajl sastoji iz više delova (što će biti slučaj za sve fajlove veće od veličine pojedničanih delova), U/I procesi treba da obradu rade paralelno, čak iako se delovi šalju jedan po jedan (običan pool.apply ovo ne zadovoljava).
Sistem treba da može da obradi fajlove koji su veći od raspoložive memorije.
get (5 boda)
Nit za obradu komande

Pronalazi fajl u registru fajlova, proverava status i dohvata ime
Dohvata listu delova datog fajla iz registra delova (identifikator, MD5 i možda još neke informacije).
Šalje ovu listu (u delovima, ili element po element) U/I procesima sa zahtevom za čitanje.
Otvora rezultujući fajl za ispis i dodaje u njega delove kad stignu iz U/I procesa.
Umesto pročitanog dela, od U/I procesa može dobiti poruku o grešci, ako se MD5 pročitanih podataka ne slaže sa očekivanim. U tom slučaju ispisuje grešku na izlazu i obustavlja čitanje.
Napomene:

U slučaju greške, sistem treba da nastavi da radi. Nit za obradu komande treba da sačeka i primi sve zahteve koje je poslala U/I procesima i da se potom uredno ugasi.
Sistem treba da može da obradi fajlove koji su veći od raspoložive memorije.
delete (4 boda)
Nit za obradu komande
Pronalazi fajl u registru fajlova, proverava status, i označava da fajl nije spreman
Dohvata listu delova datog fajla iz registra delova. Označava da delovi nisu spremni
Šalje ovu listu (u delovima, ili element po element) U/I procesima sa zahtevom za brisanje.
Svaki deo za koji stigne potvrda iz U/I procesa da je obrisan briše iz registra delova.
Briše fajl iz registra fajlova kada stigne potvrda da je poslednji deo obrisan.
list (2 boda)
Dohavata i ispisuje listu imena i identifikatora fajla koji su smešteni u sistem.
Exit (2 boda)
Gasi sistem i aktivne niti i procese.
Napomena:
Potrebno je da sistem može paraleno da procesira više komandi. Posebno voditi računa o količini zauzete memorije u toku put i get komandi.
Obezbediti da sistem vodi evidenciju koliko delova fajlova je trenutno u memoriji (u svim nitima i procesima).
Kada se potrosnja približi ograničenju, pauzirati dalji rad niti za obradu komandi, dok se broj učitanih delova fajlova ne smanji.
(Verovatno je potrebno uvesti neku deljenu promenjivu gde niti dodaju veličinu delova koje nameravaju da učitaju i istu oduzimaju kada se završi obrada tog dela. Takođe, verovatno je potrebno uvesti nekakav Uslov, kako bi niti mogle da čekaju i budu obaveštene kada se steku uslovi da nastave sa radom).

Konfiguracija
Konfiguracija sistema treba da bude izvedena kroz yaml fajl, pri čemu su bar sledeće stvari konfigurabilne:

Putanja do dirketorijuma gde se čuvaju delovi fajlova
Broj U/I procesa
Maksimalna količina memorije koju sistem može da koristi
