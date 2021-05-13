# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List

from SPARQLWrapper import SPARQLWrapper, JSON
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class SPARQL:
    @staticmethod
    def getReply(query):
        sparql = SPARQLWrapper("http://localhost:3030/ds")
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()


class ActionCourse(Action):

    def name(self) -> Text:
        return "action_course_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()

        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?description 
        WHERE {?sub a teach:Course ;
        dcterms:subject '""" + course[0] + """' ;
        dcterms:identifier '""" + course[1] + """'^^xsd:integer ;
        teach:courseDescription ?description .
          }
          """
        result = SPARQL.getReply(query)
        result = str(result["results"]["bindings"][0]["description"]["value"])
        result = "Course: '" + course[0] + " " + course[1] + "' description:\n" + result

        dispatcher.utter_message(text=f"" + result)

        return []


class ActionTopic(Action):

    def name(self) -> Text:
        return "action_topic"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        topic = str(tracker.slots['topic'])
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?courseNumber (COUNT (?resourceuri) as ?topicCount)
        WHERE { ?sub a teach:Course ;
        dcterms:identifier ?courseNumber ;
        ex:hasTopic ?topicuri .
        ?topicuri a ex:Topic ;
        dcterms:title '""" + topic + """'@en .
        ?resourceuri ex:topicCovered ?topicuri .
        } GROUP BY ?courseNumber
        ORDER BY ASC (?topicCount)
        """
        results = SPARQL.getReply(query)
        courseNum = []
        topicCount = []
        ans = "CourseNumber TopicCount"
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:
            for result in results["results"]["bindings"]:
                for key, value in result.items():
                    if key == 'courseNumber':
                        courseNum.append(str(value["value"]))
                    else:
                        topicCount.append(str(value["value"]))

        if len(courseNum) == len(topicCount):
            for i in range(0, len(courseNum)):
                ans = ans + "\n" + courseNum[i] + "\t\t" + topicCount[i]
        ans = "Topic: '" + topic + "'\n" + ans
        dispatcher.utter_message(text=ans)

        return []


class ActionCELabTopic(Action):

    def name(self) -> Text:
        return "action_course_event_lab_topics"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        number = str(tracker.slots['course_event_number'])
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?topic ?resource ?resourceUri
        WHERE {?sub a teach:Course ; 
            dcterms:subject '"""+course[0]+"""' ; 
            dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
            ex:hasLecture ?lec .
            ?lec a teach:Lecture ;
            dcterms:identifier '"""+number+"""'^^xsd:integer ;
            ex:hasLab ?lab .
            ?lab ex:hasContent ?resourceUri .
            ?resourceUri ex:topicCovered ?topicuri ;
            ex:resource ?resource .
            ?topicuri dcterms:title ?topic .
            }"""
        results = SPARQL.getReply(query)
        topic = []
        resource = []
        resourceUri = []
        ans = "Topic\tResource\tResourceURI"
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:
            for result in results["results"]["bindings"]:
                for key, value in result.items():
                    if key == 'topic':
                        topic.append(str(value["value"]))
                    elif key == 'resource':
                        resource.append(str(value["value"]))
                    else:
                        resourceUri.append(str(value["value"]))

        for i in range(0, len(topic)):
            ans = ans + "\n" + topic[i] + "\t\t" + resource[i] + "\t\t" + resourceUri[i]
        ans = f"Topics of Lab: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} :" + "'\n" + ans
        dispatcher.utter_message(text=ans)
        return []


class ActionCELectureTopic(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_topics"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        number = str(tracker.slots['course_event_number'])
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?topic ?resource ?resourceUri
        WHERE {?sub a teach:Course ; 
            dcterms:subject '"""+course[0]+"""' ; 
            dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
            ex:hasLecture ?lec .
              ?lec a teach:Lecture ;
              dcterms:identifier '"""+number+"""'^^xsd:integer ;
              ex:hasContent ?resourceUri .
              ?resourceUri ex:topicCovered ?topicuri ;
              ex:resource ?resource .
              ?topicuri dcterms:title ?topic .
              }"""
        results = SPARQL.getReply(query)
        topic = []
        resource = []
        resourceUri = []
        ans = "Topic\tResource\tResourceURI"
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:
            for result in results["results"]["bindings"]:
                for key, value in result.items():
                    if key == 'topic':
                        topic.append(str(value["value"]))
                    elif key == 'resource':
                        resource.append(str(value["value"]))
                    else:
                        resourceUri.append(str(value["value"]))

        for i in range(0, len(topic)):
            ans = ans + "\n" + topic[i] + "\t\t" + resource[i] + "\t\t" + resourceUri[i]
        ans = f"Topics of Lecture: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} :" + "'\n" + ans
        dispatcher.utter_message(text=ans)

        return []


class ActionCELabNameLink(Action):

    def name(self) -> Text:
        return "action_course_event_lab_name_link"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        number = str(tracker.slots['course_event_number'])

        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?name ?link
        WHERE {?sub a teach:Course ;
        dcterms:subject '"""+course[0]+"""' ; 
        dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
        ex:hasLecture ?lec .
        ?lec a teach:Lecture ;
        ex:hasLab ?lab.
        ?lab a ex:Lab ;
        dcterms:identifier '"""+number+"""'^^xsd:integer ;
        dcterms:title ?name ;
        ex:hasContent ?link .
        }"""
        results = SPARQL.getReply(query)
        print(results)
        ans=""
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:

            ans="Name: "+results["results"]["bindings"][0]["name"]["value"]+"\nLink: "+results["results"]["bindings"][0]["link"]["value"]

        ans=f"Name and Link of Lab: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} :\n"+ans
        dispatcher.utter_message(
            text=ans)

        return []


class ActionCELabContent(Action):

    def name(self) -> Text:
        return "action_course_event_lab_content"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course'])
        number = str(tracker.slots['course_event_number'])
        query=""""""
        results = SPARQL.getReply(query)

        dispatcher.utter_message(
            text=f"Content of Lab: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} :")

        return []


class ActionCELectureNameLink(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_name_link"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course'])
        number = str(tracker.slots['course_event_number'])
        query = """ """
        # result = SPARQL.getReply(query)

        dispatcher.utter_message(
            text=f"Name and Link of Lecture: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} :")

        return []


class ActionCELectureContent(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_content"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        number = str(tracker.slots['course_event_number'])
        query = """PREFIX ex: <http://example.org/>
                PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX teach: <http://linkedscience.org/teach/ns#>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                SELECT ?content 
                WHERE {?sub a teach:Course ;
                dcterms:subject '"""+course[0]+"""' ; 
                dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
                ex:hasLecture ?lec . 
                ?lec a teach:Lecture ;
                dcterms:identifier '"""+number+"""'^^xsd:integer ;
                ex:hasContent ?content .
                } """
        results = SPARQL.getReply(query)
        ans=""
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:
            for result in results["results"]["bindings"]:
                for key, value in result.items():
                    ans=ans+str(value["value"])+"\n"

        ans=f"Content of Lecture: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} :\n"+ans
        dispatcher.utter_message(text=ans)

        return []

class ActionCELectureLinkWorksheet(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_link_worksheet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        number = str(tracker.slots['course_event_number'])
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?worksheet 
        WHERE {?sub a teach:Course ;
        dcterms:subject '"""+course[0]+"""' ;
        dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
        ex:hasLecture ?lec .
        ?lec a teach:Lecture ;
        dcterms:identifier '"""+number+"""'^^xsd:integer ;
        ex:hasWorksheet ?worksheet .
        } """
        results = SPARQL.getReply(query)
        print(results)
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:
            ans=results["results"]["bindings"][0]["worksheet"]["value"]
        ans=f"Link of worksheet of Lecture: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} :\n"+ans
        dispatcher.utter_message(
            text=ans)

        return []


class ActionCELectureNameSlide(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_name_slide"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?name ?slides 
        WHERE {?sub a teach:Course ;
        dcterms:subject '"""+course[0]+"""' ;
        dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
        ex:hasLecture ?lec .
        ?lec a teach:Lecture ;
        dcterms:title ?name ;
        ex:hasSlide ?slides .
        }"""
        results = SPARQL.getReply(query)
        name=[]
        slides=[]
        ans="Name\tSlide\n"
        if not results["results"]["bindings"]:
            ans="Not Found."
        else:
            for result in results["results"]["bindings"]:
                for key, value in result.items():
                    if key=="name":
                        name.append(str(value["value"]))
                    else:
                        slides.append(str(value["value"]))
            for i in range(0,len(name)):
                ans = ans + name[i] + "\t"+slides[i]+"\n"

            ans=f"Name and Slides of all lectures of Course: {tracker.slots['course']} :\n"+ans
        dispatcher.utter_message(text=ans)

        return []


class ActionCELectureOther(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_other"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT (COUNT(*) as ?otherMaterialCount)
        WHERE {?sub a teach:Course ;
        dcterms:subject '"""+course[0]+"""' ;
        dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
        ex:hasLecture ?lec .
        ?lec a teach:Lecture ;
        ex:hasOtherMaterial ?material.
        }"""
        results = SPARQL.getReply(query)

        if not results["results"]["bindings"]:
            ans="Not Found."
        else:
            ans=results["results"]["bindings"][0]["otherMaterialCount"]["value"]

        ans=f"Number of lectures of Course: {tracker.slots['course']} that have other material is:\n"+ans
        dispatcher.utter_message(
            text=ans)

        return []


class ActionCELectureReading(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_reading"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        number = str(tracker.slots['course_event_number'])
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT (COUNT(*) as ?readingCount)
        WHERE {?sub a teach:Course ;
        dcterms:subject '"""+course[0]+"""' ;
        dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
        ex:hasLecture ?lec .
        ?lec a teach:Lecture ;
        ex:hasReading ?reading ;
        dcterms:identifier '"""+number+"""'^^xsd:integer .
        }"""
        results = SPARQL.getReply(query)
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:
            ans = results["results"]["bindings"][0]["readingCount"]["value"]

        ans=f"Number supplimentary readings in Lecture: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} is:\n"+ans
        dispatcher.utter_message(
            text=ans)

        return []


class ActionCELectureTopicDBLink(Action):

    def name(self) -> Text:
        return "action_course_event_lecture_topic_link"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course = str(tracker.slots['course']).split()
        number = str(tracker.slots['course_event_number'])
        query = """PREFIX ex: <http://example.org/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX teach: <http://linkedscience.org/teach/ns#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?link 
        WHERE {?sub a teach:Course ;
        dcterms:subject '"""+course[0]+"""' ;
        dcterms:identifier '"""+course[1]+"""'^^xsd:integer ;
        ex:hasLecture ?lec .
        ?lec a teach:Lecture ;
        dcterms:identifier '"""+number+"""'^^xsd:integer ;
        ex:hasContent ?content .
        ?content ex:topicCovered ?topicuri .
        ?topicuri foaf:page ?link .
        } """
        results = SPARQL.getReply(query)
        ans=""
        if not results["results"]["bindings"]:
            ans = "Not Found."
        else:
            for result in results["results"]["bindings"]:
                for key, value in result.items():
                    ans=ans+str(value["value"])+"\n"


        ans=f"DBPedia links of topics in Lecture: {tracker.slots['course_event_number']} of Course: {tracker.slots['course']} are:\n"+ans
        dispatcher.utter_message(
            text=ans)

        return []
