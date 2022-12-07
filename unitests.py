from unittest import TestCase
from rest_framework.test import APIClient
import json
import pytest
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from articles.models import Article, Tags, DocumentModel
from comments.models import Comments
from django.core.files.uploadedfile import SimpleUploadedFile



@pytest.mark.django_db
class BasicTestCommentAPI(TestCase):
    
    def setUp(self)->None:
        
        self.client=APIClient()
        #below is the comments urls using globally
        self.comments_url='/comments/'
        #below creating user and authenticating with token
        User=get_user_model()
        self.user=User.objects.create(username='dummyuser', password='Admin123!')
        self.token=Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        #Creating Tags for articles

        self.tags=Tags.objects.create(tag='javascript')

        #creating uploaded file for articles

        file=SimpleUploadedFile("readme.docx", b"file_content", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.uploaded_file=DocumentModel.objects.create(document=file)

        #Creating article for comments
        self.article=Article.objects.create(headline='test headline',
        abstract='test abstract', content='testcontent', isDraft=False,
        created_by=self.user)

        #adding files id to m2m field
        self.article.files.add(self.uploaded_file.id)
        #adding tags to m2m field
        self.article.tags.add(self.tags.id)
        #adding into user into favourites
        self.article.isFavourite.add(self.user)
        

    def tearDown(self)->None:
        pass


class TestGetCommentAPI(BasicTestCommentAPI):

    def test_zero_comments_should_return_empty_list(self)->None:

        response=self.client.get(self.comments_url)
        response_content=json.loads(response.content)
        print(response_content)

        #below asserting respponse code
        self.assertEqual(response.status_code, 200)

        #checking that empty array is being returned
        self.assertEqual(response_content, [])
        
    def test_get_one_comment(self)->None:
        
        #creating data

        comment=Comments.objects.create(article_fk=self.article,
        user_fk=self.user, comments='This is a test comment')

        #responses
        response=self.client.get(self.comments_url)
        response_content=json.loads(response.content)
        print(comment.id)


        #assert statements
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_content[0]['id'], comment.id)


class TestPostCommentApi(BasicTestCommentAPI):

    def test_post_comment_should_fail_without_arguments(self)->None:

        response=self.client.post(path=self.comments_url)

        #asserting below status code
        self.assertEqual(response.status_code, 400)

        #asserting json load equal
        self.assertEqual(json.loads(response.content), {"comments" : ["This field is required."], "article_fk": ["This field is required."], "user_fk": ["This field is required."]})

    def test_post_comment_should_fail_if_article_or_user_id_doesnt_exists(self)->None:

        #post response

        response=self.client.post(path=self.comments_url, 
        data = {
            "article_fk" : 10,
            "user_fk" : 5,
            "comments" : "Testing comments for failing"
        })

        #assert statements
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'article_fk': ['Invalid pk "10" - object does not exist.'], 'user_fk': ['Invalid pk "5" - object does not exist.'] })

    def test_post_comment_should_pass(self)->None:

        #post response
        response=self.client.post(path=self.comments_url, 
        data = {
           "article_fk" : self.article.id ,
           "user_fk" : self.user.id,
           "comments" : "Test data for posting comments for article according to user "
        })
        print(json.loads(response.content))
        #assert statements
        self.assertEqual(response.status_code, 201)
        

class TestGetPostReplyComment(BasicTestCommentAPI):

    def test_get_comment_reply(self)->None:

        #creating comments
        self.comment=Comments.objects.create(article_fk=self.article,
        user_fk=self.user, comments='This is a test comment for reply')

        #creating reply
        reply=Comments.objects.create(article_fk=self.article,
        user_fk=self.user, comments='This is a reply to comment',
        reply=self.comment)

        #reponses
        response=self.client.get(self.comments_url)
        response_replies=json.loads(response.content)[0]['replies']
        response_id=response_replies[0]['id']
    
        #assert statements
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_id, reply.id)

    def test_post_reply_on_comments_must_succeed(self)->None:

        #creating comments
        self.comment=Comments.objects.create(article_fk=self.article,
        user_fk=self.user, comments='This is a test comment for reply')

        #responses 
        response=self.client.post(path=self.comments_url,
        data = {
            "article_fk" : self.article.id,
            "user_fk": self.user.id,
            "comments": "This is a reply",
            "reply": self.comment.id
        })
        #assert statements
        self.assertEqual(response.status_code, 201)
        
