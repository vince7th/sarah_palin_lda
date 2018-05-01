# 0) Import libraries
import re
from stop_words import get_stop_words
en_stop = get_stop_words('en')
from gensim import corpora, models
import gensim
import csv 


# 1) Import and construct data
fhand = open('palindata.csv')
email_number=list()
email_pure=list()
for line in fhand:
    line = line.strip()
    key_value  = line.split(',')
    email_number.append(key_value)
    email_pure.append(key_value[1])


# 2) Processing des mails : série d'expressions régulières pour cleaner les emails
#    ainsi que pour réunir certaines chaînes de caractères sous une seule chaîne
#    comme dollar, dollars, $, deviennent 'dollarmoneyprocess'. Voici les cleanings effectués :
#
#    remove web address
#    remove emails address
#    remove digits
#    remove punctuation ():-_
#    convert $ into dollars
#    remove 2 length words and less 
#    remove stop words
email_process_list=list()
for number,email in email_number:
    email_process=[word for word in email.split() if word not in en_stop]
    email_process=' '.join(email_process)
    email_process=re.sub(ur'(http:\S+)', ' ' ,email_process)
    email_process=re.sub(ur'(www\.\S+)', ' ' ,email_process)
    email_process=re.sub(ur'\S+\.com', ' ' ,email_process)
    email_process=re.sub(ur'\S+@\S+', ' ' ,email_process)
    email_process=re.sub('\d+', '', email_process)
    email_process=re.sub(ur'\$','dollarmoneyprocess',email_process)
    email_process=re.sub(ur'[^\w\d\s\+]',' ',email_process)
    email_process=re.sub(ur'pm','timetableprocess',email_process)
    email_process=re.sub(r'\b\w{1,2}\b', ' ', email_process)
    email_process=re.sub(ur'\S+_\S*', '' ,email_process)
    email_process=re.sub(ur'_\S*', '' ,email_process)
    email_process=re.sub(ur'\s(dollars)\s','dollarmoneyprocess',email_process)
    email_process=re.sub(ur'\s(dollar)\s','dollarmoneyprocess',email_process)
    email_process=email_process.split()
    email_process=set(email_process)
    email_process_list.append((number,email_process))


# 3.a) Fréquence des mots à travers la collection d'emails
#      Les mots apparaissant dans trop de mails vont être supprimmés
words_dico=dict()
for number,email in email_process_list:
    for word in set(email):
        if word not in words_dico:
            words_dico[word]=1
        else:
            words_dico[word]=words_dico[word]+1

# 3.b) On transforme le dictionnaire précédemment crée en liste afin de pouvoir le trier
#      Affichage des 50 mots les plus fréquents
words_freq = list()
for key, val in words_dico.items():
    words_freq.append( (key, val) )
words_freq.sort(key=lambda tup: tup[1] ,reverse=True)
print words_freq[:50]


# 4.a) Les mots apparaissant dans moins de 11 mails
#    ainsi que les 30 mots les plus redondants parmi les emails
#    sont enregistrés dans une liste words_to_delete
words_to_delete1= [t[0] for t in words_freq if t[1] <11]
words_to_delete2=[t[0] for t in words_freq[:30]]
words_to_delete=words_to_delete1+words_to_delete2

# 4.b) On supprime les mots en question dans les emails
#      itera est un compteur qui va nous servir plus tard
#      ATTENTION : le temps de calcul est relativement long
#      raison pour laquelle, on sauve la liste dans une copie à la fin
email_process_list_new=list()
itera=0
for number,email in email_process_list:
    email_process=[word for word in email if word not in words_to_delete]
    email_process_list_new.append((itera,number,email_process))
    itera=itera+1

email_process_list_new2=email_process_list_new

# 4.c) On supprime les emails contenant moins de 11 mots
#      On crée une liste emailonly dans laquelle on ne stocke que les emails
#      et rien d'autre
for idx,email in enumerate(email_process_list_new2):
    if len(email[2])<11:
        del email_process_list_new2[idx]

emailsonly=[x[2] for x in email_process_list_new2]


# 5) Préparation avant lancement de la LDA, il nous faut créer deux objets gensim
#    (*) un objet dictionary qui comprend tous les mots utilisés dans l'ensemble de la 
#    collection d'emails
#    (*) un objet corpus (document term matrix) qui contient tous les emails mais sous
#    la forme de vecteurs dont les éléments sont des 1s ou des 0s. 1 si le mot est
#    présent dans le mail. 0 sinon.
dictionary = corpora.Dictionary(emailsonly)
corpus = [dictionary.doc2bow(text) for text in emailsonly]


# 6) Lancement de la LDA
ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=30, id2word = dictionary, passes=20)


# 7) On affche les topics (la distribution des 20 mots les plus fréquents qui définissent les topics)
#    On peut également sauver les résultats du modèle et reload ces résultats avec les commandes
#    save et load
ldamodel.show_topics(num_topics=30, num_words=20, log=False, formatted=True)
ldamodel.save('ldasaved')
x=ldamodel.load('ldasaved')

# 8) Distribution des topics d'un mail et son original
x.show_topics(num_topics=30, num_words=20, log=False, formatted=True)
x.get_document_topics(corpus[10], minimum_probability=None)
email_process_list_new2[10]
email_pure[11]


# 9) Sauvegarde de la distribution des mots par topic dans le fichier csv ldaoutput.csv
topx=x.show_topics(num_topics=30, num_words=20, log=False, formatted=False)
topic_word_distribution=list()
k=0
for topic in topx:
    for word in topic[1]:
        topic_word_distribution.append((k,)+word)
    k=k+1
 
with open('C:\Users\Bar Yokhai\Desktop\python\pythondir\ldaoutput_best.csv', 'w') as output:
    writer = csv.writer(output, delimiter=';',lineterminator='\n')
    for tweet in topic_word_distribution:
        writer.writerow([x.encode('utf-8') if isinstance(x, unicode) else x for x in tweet])   


# 10) On sauve les mixtures de topics des emails dans ldaemailbest.csv
topic_distribution_email=x.get_document_topics(corpus, minimum_probability=None)
empty_tuple=[0] * 32
list_email_topic_distribution=[empty_tuple[:] for _ in range(len(email_process_list_new2))]

k=0
for number,idx,email in email_process_list_new2:
    print idx
    list_email_topic_distribution[k][0]=idx
    list_email_topic_distribution[k][1]=len(email)
    for topic in topic_distribution_email[k]:
        list_email_topic_distribution[k][topic[0]+2]=topic[1]
    k=k+1

with open('ldaemailbest.csv', 'w') as output:
    writer = csv.writer(output, delimiter=';',lineterminator='\n')
    for tweet in list_email_topic_distribution:
        writer.writerow([x.encode('utf-8') if isinstance(x, unicode) else x for x in tweet])  


