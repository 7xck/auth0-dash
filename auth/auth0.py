import os
import flask
from authlib.integrations.requests_client import OAuth2Session
from urllib.parse import urlencode, urljoin

from .auth import Auth

# READ:
# all just stuff from a dummy account, no legit secrets here so I'll just leave in
# basically go create an auth0 account and  create a new project, then fill in these values
# MUST ADD THE FOLLOWING IN AUTH0 PROJECT SETTINGS:
# Allowed callback urls: http://127.0.0.1:3000/login/callback
# Allowed logout urls: http://127.0.0.1:3000/logout
# Allowed web origins: http://127.0.0.1:3000
secret_dict = {
    "AUTH0_DOMAIN": "domain",
    "APP_SECRET_KEY": "xixieieidmmcnskadsfvb",  # should probably actually generate a real key in prod...
    "AUTH0_CLIENT_ID": "client id",
    "AUTH0_CLIENT_SECRET": "client secret",
}
# add your email in here
EMAIL_DOMAINS = [
    "me@gmail.com",
    # can also just do a domain, like google.com
    # and then xyz@google.com will be auto allowed.
]

env = {
    "FLASK_SECRET_KEY": secret_dict["APP_SECRET_KEY"],
    "AUTH0_AUTH_URL": "https://" + secret_dict["AUTH0_DOMAIN"] + "/authorize",
    "AUTH0_AUTH_SCOPE": "openid profile email",
    "AUTH0_AUTH_TOKEN_URI": "https://" + secret_dict["AUTH0_DOMAIN"] + "/oauth/token",
    "AUTH0_AUTH_USER_INFO_URL": "https://" + secret_dict["AUTH0_DOMAIN"] + "/userinfo",
    "AUTH0_AUTH_CLIENT_ID": secret_dict["AUTH0_CLIENT_ID"],
    "AUTH0_AUTH_CLIENT_SECRET": secret_dict["AUTH0_CLIENT_SECRET"],
    "AUTH0_LOGOUT_URL": "https://" + secret_dict["AUTH0_DOMAIN"] + "/v2/logout",
    "AUTH0_API_AUDIENCE": "",
    "AUTH_FLASK_ROUTES": "true",
}


COOKIE_EXPIRY = 60 * 60 * 24 * 14  # Cookie timeout. When elapsed, force relog
COOKIE_AUTH_USER_NAME = "AUTH-USER"
COOKIE_AUTH_ACCESS_TOKEN = "AUTH-TOKEN"
COOKIE_AUTH_EMAIL_VERIFIED_BOOL = "False"
AUTH_STATE_KEY = "auth_state"
CLIENT_ID = env.get("AUTH0_AUTH_CLIENT_ID")
CLIENT_SECRET = env.get("AUTH0_AUTH_CLIENT_SECRET")
LOGOUT_URL = env.get("AUTH0_LOGOUT_URL")
AUTH_REDIRECT_URI = "/login/callback"
AUTH_FLASK_ROUTES = env.get("AUTH_FLASK_ROUTES", "true")

if AUTH_FLASK_ROUTES == "true":
    AUTH_FLASK_ROUTES = True
elif AUTH_FLASK_ROUTES == "false":
    AUTH_FLASK_ROUTES = False
else:
    print(
        f"warning: AUTH_FLASK_ROUTES is set to {AUTH_FLASK_ROUTES}. Must be 'true' or 'false', otherwise will raise this warning and be set to False."
    )
    AUTH_FLASK_ROUTES = False


class Auth0Auth(Auth):
    def __init__(self, app):
        Auth.__init__(self, app)
        app.server.config["SECRET_KEY"] = env.get("FLASK_SECRET_KEY")
        app.server.config["SESSION_TYPE"] = "filesystem"

        @app.server.route("/login/callback")
        def callback():
            return self.login_callback()

        @app.server.route("/unverified")
        def unverified():
            return self.unverified()

        @app.server.route("/forbidden")
        def forbidden():
            return self.forbidden()

        @app.server.route("/logout/")
        def logout():
            return self.logout()

    def is_authorized(self):
        user = flask.request.cookies.get(COOKIE_AUTH_USER_NAME)
        token = flask.request.cookies.get(COOKIE_AUTH_ACCESS_TOKEN)
        verified_bool = flask.request.cookies.get(COOKIE_AUTH_EMAIL_VERIFIED_BOOL)

        if not user or not token:
            return False
        elif verified_bool == "False":
            return "Not Verified"
        return flask.session.get(user) == token

    def login_request(self):
        redirect_uri = urljoin(flask.request.base_url, AUTH_REDIRECT_URI).replace(
            "http://", "http://"
        )  # replace with https if using SSL

        session = OAuth2Session(
            CLIENT_ID,
            CLIENT_SECRET,
            scope=env.get("AUTH0_AUTH_SCOPE"),
            redirect_uri=redirect_uri.replace("http://", "http://"),
        )

        uri, state = session.create_authorization_url(
            env.get("AUTH0_AUTH_URL"), audience=env.get("AUTH0_API_AUDIENCE")
        )

        flask.session["REDIRECT_URL"] = flask.request.url.replace("http://", "http://")
        flask.session[AUTH_STATE_KEY] = state
        flask.session.permanent = False

        return flask.redirect(uri, code=302)

    def auth_wrapper(self, f):
        def wrap(*args, **kwargs):
            if AUTH_FLASK_ROUTES:
                if not self.is_authorized():
                    return flask.redirect("/")
                elif self.is_authorized() == "Not Verified":
                    return flask.redirect("/unverified")
            response = f(*args, **kwargs)
            return response

        return wrap

    def index_auth_wrapper(self, original_index):
        def wrap(*args, **kwargs):
            if self.is_authorized():
                return original_index(*args, **kwargs)
            elif self.is_authorized() == "Not Verified":
                return flask.redirect("/unverified")
            else:
                return self.login_request()

        return wrap

    def login_callback(self):
        if "error" in flask.request.args:
            if flask.request.args.get("error") == "access_denied":
                return "You denied access."
            return "Error encountered."

        if "code" not in flask.request.args and "state" not in flask.request.args:
            return self.login_request()
        else:
            # user is successfully authenticated
            auth0 = self.__get_auth(state=flask.session[AUTH_STATE_KEY])
            try:
                token = auth0.fetch_token(
                    env.get("AUTH0_AUTH_TOKEN_URI"),
                    client_secret=CLIENT_SECRET,
                    authorization_response=flask.request.url,
                )
                print(token["id_token"])
                print(token["access_token"])
            except Exception as e:
                return e.__dict__

            auth0 = self.__get_auth(token=token)
            resp = auth0.get(env.get("AUTH0_AUTH_USER_INFO_URL"))
            if resp.status_code == 200:
                user_data = resp.json()
                user_name = user_data["name"]
                email = user_data["email"]
                if not any(domain in email for domain in EMAIL_DOMAINS):  # user_name
                    r = flask.redirect("/forbidden")
                    r.set_cookie(
                        COOKIE_AUTH_USER_NAME, user_data["email"], max_age=COOKIE_EXPIRY
                    )
                    return r
                elif user_data["email_verified"] == False:
                    r = flask.redirect("/unverified")
                    r.set_cookie(
                        COOKIE_AUTH_USER_NAME, user_data["email"], max_age=COOKIE_EXPIRY
                    )
                    return r
                r = flask.redirect(flask.session["REDIRECT_URL"])
                r.set_cookie(
                    COOKIE_AUTH_USER_NAME, user_data["email"], max_age=COOKIE_EXPIRY
                )
                r.set_cookie(
                    COOKIE_AUTH_EMAIL_VERIFIED_BOOL,
                    str(user_data["email_verified"]),
                    max_age=COOKIE_EXPIRY,
                )
                r.set_cookie(
                    COOKIE_AUTH_ACCESS_TOKEN,
                    token["access_token"],
                    max_age=COOKIE_EXPIRY,
                )
                flask.session[user_data["email"]] = token["access_token"]  # email?
                return r

            return "Could not fetch your information."

    @staticmethod
    def __get_auth(state=None, token=None):
        if token:
            return OAuth2Session(CLIENT_ID, token=token)
        if state:
            return OAuth2Session(
                CLIENT_ID,
                state=state,
                redirect_uri=urljoin(flask.request.base_url, AUTH_REDIRECT_URI).replace(
                    "http://", "http://"
                ),
            )
        return OAuth2Session(
            CLIENT_ID,
            redirect_uri=urljoin(flask.request.base_url, AUTH_REDIRECT_URI).replace(
                "http://", "http://"
            ),
        )

    @staticmethod
    def logout():
        # Clear session stored data
        flask.session.clear()

        # Redirect user to logout endpoint
        return_url = flask.request.host_url
        params = {"returnTo": return_url, "client_id": CLIENT_ID}
        r = flask.redirect(LOGOUT_URL + "?" + urlencode(params))
        r.delete_cookie(COOKIE_AUTH_USER_NAME)
        r.delete_cookie(COOKIE_AUTH_ACCESS_TOKEN)

        return r

    @staticmethod
    def unverified():
        return f"""You need to verify your email before you can access the dash,  {flask.request.cookies.get(COOKIE_AUTH_USER_NAME)}
        <br>
        Please check your email for a verification link. After you have verified your email, come back here and relogin
        <br>
        <a href="/logout/">Relogin</a>
        """

    @staticmethod
    def forbidden():
        return f"""
        Your email, {flask.request.cookies.get(COOKIE_AUTH_USER_NAME)} is not
        one of the approved domains. Please register and log in in with your approved email.
        <br>
        <a href="/logout/">Relogin</a>
        """
