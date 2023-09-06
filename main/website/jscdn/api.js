let urs = new URL(location.href)
let pathqs = urs.pathname + urs.search + urs.hash

let ratelimit = `<iframe src="/rlm" frameborder="0"
style="overflow:hidden;overflow-x:hidden;overflow-y:hidden;height:100%;width:100%;position:absolute;top:0%;left:0px;right:0px;bottom:0px"
height="100%" width="100%"></iframe>`;

function create_UUID(){
    var dt = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (dt + Math.random()*16)%16 | 0;
        dt = Math.floor(dt/16);
        return (c=='x' ? r :(r&0x3|0x8)).toString(16);
    });
    return uuid;
}

let usercache = null

function getuser(loginreq=false) {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/api/@me", false );
    xmlHttp.send( null );
    if (xmlHttp.status == 429) {
        document.body.innerHTML = ratelimit;
        throw Error("Rate Limit");
    } else if (xmlHttp.status == 401) {
        if (loginreq) {
            if (document.cookie.indexOf('Session_Token=') != -1) {
                document.cookie = "Session_Token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            }
            location.replace(`/login?u=${encodeURIComponent(pathqs)}`)
        }
    }
    return xmlHttp
}

function getlogin() {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/api/login", false );
    xmlHttp.send( null );
    if (xmlHttp.status == 429) {
        document.body.innerHTML = ratelimit;
        throw Error("Rate Limit")
    }
    return xmlHttp
}

function getserver() {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", "/api/@me/guilds", false );
    xmlHttp.send( null );
    if (xmlHttp.status == 429) {
        document.body.innerHTML = ratelimit;
        throw Error("Rate Limit")
    }
    return xmlHttp
}

function sidcheck() {
    document.cookie = `sid=${create_UUID()}`;
}

function check_login() {
    if (location.hostname != "fantasybot.tech") {
        location.replace(`https://fantasybot.tech`)
    }
    if (getlogin().status === 401) {
        if (document.cookie.indexOf('Session_Token=') != -1) {
            document.cookie = "Session_Token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        }
        location.replace(`/login?u=${encodeURIComponent(pathqs)}`)
    } else {
        sidcheck()
    }
}

function servernameicon(name) {
    return name.split(/\s/).reduce((response,word)=> response+=word.slice(0,1),'')
}

