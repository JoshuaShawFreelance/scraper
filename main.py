from flask import Flask, render_template, request, send_file, session, redirect, jsonify, Response, make_response
from constants import MAX_FEED_LENGTH
from _thread import start_new_thread
from scraper import start_scraper
import json
import os
import hashlib
import pickle

app = Flask(__name__)
app.secret_key = b'change this for production'


#  TODO: cookie based uuid
#  TODO: html code
#  TODO: gunicorn + nginx integration


@app.route('/', methods=["GET"])
def index():
    resp = make_response(render_template("index.html"))
    resp.set_cookie('userID', get_uuid(request))
    return resp


@app.route('/settings', methods=["GET"])
def settings():
    resp = make_response(render_template("settings.html"))  # Need to change
    resp.set_cookie('userID', get_uuid(request))
    return resp


@app.route('/saved', methods=["GET"])
def saved():
    resp = make_response(render_template("saved.html"))  # Need to change
    resp.set_cookie('userID', get_uuid(request))
    return resp


@app.route('/read', methods=["GET"])
def read():
    resp = make_response(render_template("read.html"))  # Need to change
    resp.set_cookie('userID', get_uuid(request))
    return resp


@app.route('/skipped', methods=["GET"])
def skipped():
    resp = make_response(render_template("skipped.html"))  # Need to change
    resp.set_cookie('userID', get_uuid(request))
    return resp


@app.route("/post", methods=["POST"])
def post():
    userid = get_uuid(request)
    json_data = request.get_json()
    print(json_data)
    if not os.path.isfile("users.data"):
        pickle.dump({}, open("users.data", "wb"))
    userdata = pickle.load(open("users.data", "rb"))
    if userid not in userdata:
        userdata[userid] = {"saved": [], "skipped": [], "read": [], "tags": {}, "url_dict": {}, "sources": ["memeorandum", "BBC News - England", "UK News - The latest headlines from the UK | Sky News", "RNZ New Zealand Headlines"]}
    if type(json_data) != dict or "request_type" not in json_data:
        return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')
    elif json_data["request_type"] == "feed":
        """
        Returning feed (User-Based)
        """
        if os.path.isfile("news_collated.data"):
            return Response(json.dumps(first_n_elems(sorted(pickle.load(open("news_collated.data", "rb")), key=lambda i: i['published_parsed'], reverse=True), MAX_FEED_LENGTH)),
                            status=200, mimetype='application/json')
        else:
            return Response(json.dumps([]), status=200, mimetype='application/json')
    elif json_data["request_type"] == "uuid":
        return Response(json.dumps({"uuid": userid}), status=200, mimetype='application/json')
    elif json_data["request_type"] == "set_url_dict":
        if "url_dict" not in json_data or type(json_data["url_dict"]) != dict:
            return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')
        else:
            """
            Saving url_dict (User-Based)
            """
            userdata[userid]["url_dict"] = json_data["url_dict"]
            pickle.dump(userdata, open("users.data", "wb"))
            return Response(json.dumps({'Success': True}), status=200, mimetype='application/json')
    elif json_data["request_type"] == "set_saved":
        if "url_list" not in json_data or type(json_data["url_list"]) != list:
            return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')
        else:
            """
            Saving Saves (User-Based)
            """
            userdata[userid]["saved"] = json_data["url_list"]
            pickle.dump(userdata, open("users.data", "wb"))
            return Response(json.dumps({'Success': True}), status=200, mimetype='application/json')
    elif json_data["request_type"] == "set_read":
        if "url_list" not in json_data or type(json_data["url_list"]) != list:
            return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')
        else:
            """
            Saving Reads (User-Based)
            """
            userdata[userid]["read"] = json_data["url_list"]
            pickle.dump(userdata, open("users.data", "wb"))
            return Response(json.dumps({'Success': True}), status=200, mimetype='application/json')
    elif json_data["request_type"] == "set_skipped":
        if "url_list" not in json_data or type(json_data["url_list"]) != list:
            return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')
        else:
            """
            Saving Skips (User-Based)
            """
            userdata[userid]["skipped"] = json_data["url_list"]
            pickle.dump(userdata, open("users.data", "wb"))
            return Response(json.dumps({'Success': True}), status=200, mimetype='application/json')
    elif json_data["request_type"] == "set_tags":
        if "tags" not in json_data or type(json_data["tags"]) != dict:
            return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')
        """
        Saving Tags (User-Based)
        """
        userdata[userid]["tags"] = json_data["tags"]
        pickle.dump(userdata, open("users.data", "wb"))
        return Response(json.dumps({'Success': True}), status=200, mimetype='application/json')
    elif json_data["request_type"] == "set_sources":
        if "sources" not in json_data or type(json_data["sources"]) != list:
            return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')
        else:
            """
            Saving Sources (User-Based)
            """
            userdata[userid]["sources"] = json_data["sources"]
            pickle.dump(userdata, open("users.data", "wb"))
            return Response(json.dumps({'Success': True}), status=200, mimetype='application/json')
    elif json_data["request_type"] == "get_info":
        print([json.dumps(userdata[userid])])
        return Response(json.dumps(userdata[userid]), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({'Error': 'Bad Request'}), status=400, mimetype='application/json')


"""
POST JSON to /post endpoint
Example:
POSTed JSON                 ->    response JSON
 
{"request_type": "uuid"}    ->    {"uuid": "f16aac323c5e63f91b8b21c2764ef5bc"}  (not needed, just for debugging)
>>> requests.post("http://localhost/post", json={"request_type": "uuid"}).text

{"request_type": "feed"}  -> [{"title": "Covid: Raab defends \'targeted\' new coronavirus measures", "link": "https://www.bbc.co.uk/news/uk-54260259", "published": "Wed, 23 Sep 2020 12:35:07 GMT", "source": "BBC News - England"}, {"title": "Cleaner Aurora Iacomi jailed for spiking boss\'s coffee with detergent", "link": "https://www.bbc.co.uk/news/uk-england-london-54261932", "published": "Wed, 23 Sep 2020 14:25:42 GMT", "source": "BBC News - England"}, {"title": "Richmond School teacher Dave Clark killed by cows", "link": "https://www.bbc.co.uk/news/uk-england-york-north-yorkshire-54261829", "published": "Wed, 23 Sep 2020 06:13:37 GMT", "source": "BBC News - England"}, {"title": "Grimsby dismembered foot woman still unidentified", "link": "https://www.bbc.co.uk/news/uk-england-humber-54266920", "published": "Wed, 23 Sep 2020 13:28:17 GMT", "source": "BBC News - England"}, {"title": "Richard Morris: Cause of diplomat\'s death \'not yet known\'", "link": "https://www.bbc.co.uk/news/uk-england-hampshire-54264439", "published": "Wed, 23 Sep 2020 10:53:51 GMT", "source": "BBC News - England"}, {"title": "Skegness murder arrest made after man found dying in street", "link": "https://www.bbc.co.uk/news/uk-england-lincolnshire-54265169", "published": "Wed, 23 Sep 2020 11:22:58 GMT", "source": "BBC News - England"}, {"title": "Colston Hall music venue renamed Bristol Beacon", "link": "https://www.bbc.co.uk/news/uk-england-bristol-54240812", "published": "Wed, 23 Sep 2020 10:32:12 GMT", "source": "BBC News - England"}, {"title": "Manchester Arena Inquiry: Music \'was Olivia Campbell-Hardy\'s life\'", "link": "https://www.bbc.co.uk/news/uk-england-manchester-54263787", "published": "Wed, 23 Sep 2020 11:32:44 GMT", "source": "BBC News - England"}, {"title": "Yew Trees hospital: Ten staff suspended at mental health unit", "link": "https://www.bbc.co.uk/news/uk-england-essex-54255514", "published": "Wed, 23 Sep 2020 12:16:51 GMT", "source": "BBC News - England"}, {"title": "Nottinghamshire firefighters remain at 200-tonne rubbish blaze", "link": "https://www.bbc.co.uk/news/uk-england-nottinghamshire-54264650", "published": "Wed, 23 Sep 2020 10:16:12 GMT", "source": "BBC News - England"}, {"title": "Migrants: More people arrive in September than all of 2019", "link": "https://www.bbc.co.uk/news/uk-england-kent-54266961", "published": "Wed, 23 Sep 2020 13:18:43 GMT", "source": "BBC News - England"}, {"title": "Wythenshawe stabbing: Murder probe launched after man\'s death", "link": "https://www.bbc.co.uk/news/uk-england-manchester-54261640", "published": "Wed, 23 Sep 2020 06:26:46 GMT", "source": "BBC News - England"}, {"title": "Blackpool crowds ignore Covid \'last blast\' warning", "link": "https://www.bbc.co.uk/news/uk-england-lancashire-54224544", "published": "Sun, 20 Sep 2020 13:32:37 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: \'Why can I meet my mum in a pub but not her home?\'", "link": "https://www.bbc.co.uk/news/uk-england-birmingham-54175235", "published": "Tue, 22 Sep 2020 14:47:44 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: What are social distancing and self-isolation rules?", "link": "https://www.bbc.co.uk/news/uk-51506729", "published": "Tue, 22 Sep 2020 14:39:46 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: Behind the rise in cases in five charts", "link": "https://www.bbc.co.uk/news/health-54064347", "published": "Wed, 09 Sep 2020 17:01:59 GMT", "source": "BBC News - England"}, {"title": "Covid rules: Which areas have new coronavirus lockdowns?", "link": "https://www.bbc.co.uk/news/uk-england-52934822", "published": "Mon, 21 Sep 2020 16:34:55 GMT", "source": "BBC News - England"}, {"title": "Covid-19 in the UK: How many coronavirus cases are there in your area?", "link": "https://www.bbc.co.uk/news/uk-51768274", "published": "Tue, 22 Sep 2020 17:51:41 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: What are the UK travel quarantine rules?", "link": "https://www.bbc.co.uk/news/explainers-52544307", "published": "Thu, 17 Sep 2020 16:51:26 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: \\u2018It\\u2019s unfair to blame young people for virus rise\\u2019", "link": "https://www.bbc.co.uk/news/newsbeat-54076937", "published": "Tue, 08 Sep 2020 15:57:00 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: What happens if I\'m in an area on the watchlist?", "link": "https://www.bbc.co.uk/news/uk-england-53582393", "published": "Sat, 01 Aug 2020 23:46:04 GMT", "source": "BBC News - England"}, {"title": "Should office workers be heading back in?", "link": "https://www.bbc.co.uk/news/uk-england-suffolk-53888733", "published": "Tue, 25 Aug 2020 10:33:24 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: Suffolk virtual art classes \'inspired me to follow my dreams\'", "link": "https://www.bbc.co.uk/news/uk-england-suffolk-54264749", "published": "Wed, 23 Sep 2020 09:23:08 GMT", "source": "BBC News - England"}, {"title": "Birmingham football club for Muslim women", "link": "https://www.bbc.co.uk/news/uk-england-birmingham-54269218", "published": "Wed, 23 Sep 2020 14:12:06 GMT", "source": "BBC News - England"}, {"title": "Blind downhill mountain biker aims to turn professional", "link": "https://www.bbc.co.uk/news/uk-england-berkshire-54235407", "published": "Tue, 22 Sep 2020 23:02:43 GMT", "source": "BBC News - England"}, {"title": "Kingsbridge artist drawing a line over coronavirus", "link": "https://www.bbc.co.uk/news/uk-england-devon-54251880", "published": "Tue, 22 Sep 2020 23:02:47 GMT", "source": "BBC News - England"}, {"title": "Four-year-old surfer shows off his skills at Westward Ho!", "link": "https://www.bbc.co.uk/news/uk-england-devon-54251036", "published": "Tue, 22 Sep 2020 13:22:20 GMT", "source": "BBC News - England"}, {"title": "Wolves sign right-back Semedo from Barcelona in \\u00a337m deal", "link": "https://www.bbc.co.uk/sport/football/54262570", "published": "Wed, 23 Sep 2020 09:34:03 GMT", "source": "BBC News - England"}, {"title": "Coronavirus: EFL \'deeply frustrated\' as plans for limited fans return are halted", "link": "https://www.bbc.co.uk/sport/football/54269398", "published": "Wed, 23 Sep 2020 13:57:03 GMT", "source": "BBC News - England"}, {"title": "Lewis Hamilton named in Time magazine\'s 100 most influential people of 2020 list", "link": "https://www.bbc.co.uk/sport/formula1/54270693", "published": "Wed, 23 Sep 2020 14:47:27 GMT", "source": "BBC News - England"}, {"title": "Hamburg Open: Dan Evans loses to Stefanos Tsitsipas before French Open", "link": "https://www.bbc.co.uk/sport/tennis/54238537", "published": "Wed, 23 Sep 2020 14:51:16 GMT", "source": "BBC News - England"}, {"title": "Second lockdown could be needed if new restrictions don\'t work - Raab", "link": "http://news.sky.com/story/coronavirus-second-lockdown-could-be-needed-if-new-covid-19-restrictions-dont-work-warns-dominic-raab-12079186", "published": "Wed, 23 Sep 2020 08:07:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Record 486 people test positive for coronavirus in a day in Scotland", "link": "http://news.sky.com/story/coronavirus-scotland-sees-record-486-people-test-positive-in-a-day-12079451", "published": "Wed, 23 Sep 2020 12:44:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Captain Sir Tom Moore signs film deal - and wants Michael Caine or Anthony Hopkins to play him", "link": "http://news.sky.com/story/captain-sir-tom-moore-signs-film-deal-and-wants-michael-caine-or-anthony-hopkins-to-play-him-12079364", "published": "Wed, 23 Sep 2020 11:19:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "\'Unseemly and unjustified\': PM hits back at attacks on testing boss", "link": "http://news.sky.com/story/coronavirus-boris-johnson-defends-testing-boss-dido-harding-and-hits-back-at-unseemly-attacks-12079452", "published": "Wed, 23 Sep 2020 12:25:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Woman arrested on suspicion of murder after man dies in house fire", "link": "http://news.sky.com/story/woman-arrested-on-suspicion-of-murder-after-man-dies-in-greater-manchester-house-fire-12079479", "published": "Wed, 23 Sep 2020 13:21:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "500 students told to isolate after suspected COVID outbreak in halls of residence", "link": "http://news.sky.com/story/coronavirus-500-dundee-students-told-to-isolate-after-suspected-covid-outbreak-in-halls-of-residence-12079184", "published": "Wed, 23 Sep 2020 07:51:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Husband says wife\'s brain cancer progressed after lockdown stopped treatment", "link": "http://news.sky.com/story/coronavirus-husband-says-wifes-brain-cancer-progressed-after-her-chemotherapy-was-stopped-during-lockdown-12079293", "published": "Wed, 23 Sep 2020 10:29:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Holiday firms urged to refund customers who cannot travel due to lockdowns", "link": "http://news.sky.com/story/coronavirus-holiday-firms-urged-to-refund-customers-who-cannot-travel-due-to-local-lockdowns-12079437", "published": "Wed, 23 Sep 2020 12:12:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Lockdown came \'too slow\' so \'act quickly\' if another needed, government urged", "link": "http://news.sky.com/story/coronavirus-first-lockdown-came-too-slow-so-act-quickly-if-another-needed-government-urged-12079308", "published": "Wed, 23 Sep 2020 10:13:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Social distancing rules relaxed for couples in \'established relationships\'", "link": "http://news.sky.com/story/coronavirus-social-distancing-rules-relaxed-for-couples-in-established-relationships-12079505", "published": "Wed, 23 Sep 2020 13:36:00 +0100", "source": "UK News - The latest headlines from the UK | Sky News"}, {"title": "Grieving family still feeling let down by hall of residence operator", "link": "https://www.rnz.co.nz/news/national/426766/grieving-family-still-feeling-let-down-by-hall-of-residence-operator", "published": "Wed, 23 Sep 2020 20:57:16 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Nearly half of Christchurch recycling contaminated, heads to landfill", "link": "https://www.rnz.co.nz/news/national/426761/nearly-half-of-christchurch-recycling-contaminated-heads-to-landfill", "published": "Wed, 23 Sep 2020 20:02:05 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Abuse in care inquiry: Man says placements became a training ground for jail", "link": "https://www.rnz.co.nz/news/national/426752/abuse-in-care-inquiry-man-says-placements-became-a-training-ground-for-jail", "published": "Wed, 23 Sep 2020 18:36:50 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "\'Extremely traumatic\' kidnapping: CCTV footage released", "link": "https://www.rnz.co.nz/news/national/426754/extremely-traumatic-kidnapping-cctv-footage-released", "published": "Wed, 23 Sep 2020 20:38:33 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "New Covid cases sat near infected man on domestic flight - Hipkins", "link": "https://www.rnz.co.nz/news/national/426753/new-covid-cases-sat-near-infected-man-on-domestic-flight-hipkins", "published": "Wed, 23 Sep 2020 18:45:58 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Cruise ship company wants to offer \'bubble\' trips around NZ", "link": "https://www.rnz.co.nz/national/programmes/checkpoint/audio/2018765313/cruise-ship-company-wants-to-offer-bubble-trips-around-nz", "published": "Wed, 23 Sep 2020 19:27:44 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Companies fined for importing dangerous toys", "link": "https://www.rnz.co.nz/news/national/426762/companies-fined-for-importing-dangerous-toys", "published": "Wed, 23 Sep 2020 20:02:06 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Medicinal cannabis still not favoured by doctors", "link": "https://www.rnz.co.nz/news/national/426757/medicinal-cannabis-still-not-favoured-by-doctors", "published": "Wed, 23 Sep 2020 19:27:44 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Spy camera case: Police appeal suppression of former government employee", "link": "https://www.rnz.co.nz/news/national/426737/spy-camera-case-police-appeal-suppression-of-former-government-employee", "published": "Wed, 23 Sep 2020 15:47:27 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Three new cases of Covid-19 today, six historical cases reported", "link": "https://www.rnz.co.nz/news/national/426728/three-new-cases-of-covid-19-today-six-historical-cases-reported", "published": "Wed, 23 Sep 2020 13:51:58 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Repair to Napier pipe seeping sewage into ocean faces delays", "link": "https://www.rnz.co.nz/news/national/426750/repair-to-napier-pipe-seeping-sewage-into-ocean-faces-delays", "published": "Wed, 23 Sep 2020 17:58:38 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Group appeals controversial shipping channel plan", "link": "https://www.rnz.co.nz/news/national/426749/group-appeals-controversial-shipping-channel-plan", "published": "Wed, 23 Sep 2020 17:26:16 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Schools fear knock-on effect of foreign student loss", "link": "https://www.rnz.co.nz/news/national/426723/schools-fear-knock-on-effect-of-foreign-student-loss", "published": "Wed, 23 Sep 2020 12:09:39 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Man faces charges relating to offending in Gloriavale community", "link": "https://www.rnz.co.nz/news/national/426733/man-faces-charges-relating-to-offending-in-gloriavale-community", "published": "Wed, 23 Sep 2020 14:48:40 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Auckland Harbour Bridge temporary repair completed", "link": "https://www.rnz.co.nz/news/national/426700/auckland-harbour-bridge-temporary-repair-completed", "published": "Wed, 23 Sep 2020 15:16:30 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "School bus driver killed in collison loved by students - former employer", "link": "https://www.rnz.co.nz/news/national/426726/school-bus-driver-killed-in-collison-loved-by-students-former-employer", "published": "Wed, 23 Sep 2020 12:54:02 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Wellington Hospital mental health unit unsafe for staff, patients - union", "link": "https://www.rnz.co.nz/news/national/426710/wellington-hospital-mental-health-unit-unsafe-for-staff-patients-union", "published": "Wed, 23 Sep 2020 10:18:29 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Transport Agency moves to stamp out dodgy seatbelt repairs", "link": "https://www.rnz.co.nz/news/national/426706/transport-agency-moves-to-stamp-out-dodgy-seatbelt-repairs", "published": "Wed, 23 Sep 2020 09:09:25 +1200", "source": "RNZ New Zealand Headlines"}, {"title": "Kentucky attorney general to announce Breonna Taylor decision this afternoon (Courier-Journal)", "link": "http://www.memeorandum.com/200923/p61#a200923p61", "published": "Wed, 23 Sep 2020 11:00:38 -0400", "source": "memeorandum"}, {"title": "Dear Donald, Dear Mr. President: A Trump-Nixon \'80s tale (Nancy Benac/Associated Press)", "link": "http://www.memeorandum.com/200923/p60#a200923p60", "published": "Wed, 23 Sep 2020 11:00:38 -0400", "source": "memeorandum"}, {"title": "In Michigan and Pennsylvania, the Democrats Plan to Cheat (Ned Ryun/American Greatness)", "link": "http://www.memeorandum.com/200923/p62#a200923p62", "published": "Wed, 23 Sep 2020 11:00:38 -0400", "source": "memeorandum"}, {"title": "DOJ to Seek Congressional Curbs on Immunity for Internet Companies (Wall Street Journal)", "link": "http://www.memeorandum.com/200923/p58#a200923p58", "published": "Wed, 23 Sep 2020 10:50:39 -0400", "source": "memeorandum"}, {"title": "Black Lives Matter Founders Alicia Garza, Patrisse Cullors and Opal Tometi (Sybrina Fulton/TIME)", "link": "http://www.memeorandum.com/200923/p59#a200923p59", "published": "Wed, 23 Sep 2020 10:50:39 -0400", "source": "memeorandum"}, {"title": "Hunter Biden\'s Business Dealings Created \'Counterintelligence And Extortion Concerns,\' Senate Report Says (Chuck Ross/The Daily Caller)", "link": "http://www.memeorandum.com/200923/p57#a200923p57", "published": "Wed, 23 Sep 2020 10:50:39 -0400", "source": "memeorandum"}, {"title": "The Changing Racial and Ethnic Composition of the U.S. Electorate (Pew Research Center)", "link": "http://www.memeorandum.com/200923/p56#a200923p56", "published": "Wed, 23 Sep 2020 10:41:57 -0400", "source": "memeorandum"}, {"title": "Late-stage study of first single-shot vaccine begins in US (Linda A. Johnson/Associated Press)", "link": "http://www.memeorandum.com/200923/p55#a200923p55", "published": "Wed, 23 Sep 2020 10:35:02 -0400", "source": "memeorandum"}, {"title": "Pelosi unveils Watergate-style anti-corruption reforms - tailored for the Trump era (Kyle Cheney/Politico)", "link": "http://www.memeorandum.com/200923/p54#a200923p54", "published": "Wed, 23 Sep 2020 10:30:00 -0400", "source": "memeorandum"}, {"title": "Senate Report Details Hunter Biden\'s Extensive Foreign Business Dealings - and Obama Officials\' Efforts to Ignore Them (Jack Crowe/National Review)", "link": "http://www.memeorandum.com/200923/p51#a200923p51", "published": "Wed, 23 Sep 2020 10:25:06 -0400", "source": "memeorandum"}, {"title": "Liberal Bias and All, Social Media Is Still Conservatives\' Best Electoral Tool (Rick Santorum/National Review)", "link": "http://www.memeorandum.com/200923/p53#a200923p53", "published": "Wed, 23 Sep 2020 10:25:06 -0400", "source": "memeorandum"}, {"title": "The Victims Of Violence During The Kenosha Protests Are Suing Facebook (BuzzFeed News)", "link": "http://www.memeorandum.com/200923/p52#a200923p52", "published": "Wed, 23 Sep 2020 10:25:06 -0400", "source": "memeorandum"}, {"title": "Ilhan Omar fires back after Trump\'s rally attack: \'This is my country\' (Brie Stimson/Fox News)", "link": "http://www.memeorandum.com/200923/p50#a200923p50", "published": "Wed, 23 Sep 2020 10:20:02 -0400", "source": "memeorandum"}, {"title": "Facebook will let Trump run ads on election night prematurely claiming victory (Mark Sullivan/Fast Company)", "link": "http://www.memeorandum.com/200923/p49#a200923p49", "published": "Wed, 23 Sep 2020 10:20:02 -0400", "source": "memeorandum"}, {"title": "Ted Cruz blocks a U.S. Senate resolution to honor Ruth Bader Ginsburg, citing a \\"partisan\\" amendment (Abby Livingston/The Texas Tribune)", "link": "http://www.memeorandum.com/200923/p47#a200923p47", "published": "Wed, 23 Sep 2020 10:10:00 -0400", "source": "memeorandum"}]
>>> requests.post("http://localhost/post", json={"request_type": "feed"}).text

{"request_type": "set_saved", "url_list": ["url1", "url2", "url3"]}  -> {"Success": true}
>>> requests.post("http://localhost/post", json={"request_type": "set_saved", "url_list": ["url1", "url2", "url3"]}).text

{"request_type": "set_skipped", "url_list": ["url4", "url5", "url6"]}  -> {"Success": true}
>>> requests.post("http://localhost/post", json={"request_type": "set_skipped", "url_list": ["url4", "url5", "url6"]}).text

{"request_type": "set_tags", "tags": {"url1": ["test", "tag2"], "url2": ["tag3", "tag4"]}}  ->  {"Success": true}
>>> requests.post("http://localhost/post", json={"request_type": "set_tags", "tags": {"url1": ["test", "tag2"], "url2": ["tag3", "tag4"]}}).text

{"request_type": "get_info"}  ->  {"saved": ["url1", "url2", "url3"], "skipped": [], "tags": {}}
>>> requests.post("http://localhost/post", json={"request_type": "get_info"}).text

You will need to run get_info before posting set_likes, dislikes or tags as set_likes etc. all override.
E.g. if you post set_likes with an empty url_list, you will undo all your likes etc.
"""


def get_uuid_basic(request) -> str:
    """
    Primitive method for generating a unique user identifier. I'll make a cookie based one too
    + Doesn't require cookies (or cookie notice)
    - Thinks it's a new user if you change your browser, or ip
    :param request:
    :return:
    """
    return hashlib.md5(bytes(request.remote_addr + request.headers.get('User-Agent'), "utf-8")).hexdigest()


def get_uuid(request) -> str:
    user_id = request.cookies.get('userID')
    if not user_id:
        user_id = get_uuid_basic(request)
    return user_id


def first_n_elems(my_list, n):
    if n > len(my_list):
        return my_list[:len(my_list)]
    else:
        return my_list[:n]


if __name__ == "__main__":
    start_new_thread(start_scraper, ())
    app.run(host="0.0.0.0", port="80")  # Change this for production, use gunicorn and nginx instead
    # app.run("0.0.0.0")
