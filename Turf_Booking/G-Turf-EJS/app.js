/* Including Express */

const express = require("express")

const app = express()
const fs = require('fs');

const nodemailer = require('nodemailer');

const crypto = require('crypto')

/* MongoDB Connection Requirements */
const {MongoClient} = require('mongodb');
let { Collection } = require('mongoose');

const url="mongodb://127.0.0.1:27017/"

let dbname = "test"

let dbcollection = "movies"

let result,p

const filePath = "C:/java_prog/xlsheet/data.json";

const client = new MongoClient(url);

/* including bodyparser */
const body_parser=require("body-parser")
app.use(body_parser.urlencoded({extended:true}))

/* including EJS */
const ejs = require('ejs')  

/* Helps to use the CSS, images file  */
app.use(express.static("public"))

app.set("view engine","ejs")

const { Navigator } = require("node-navigator");
const navigator = new Navigator();

let locls="active";
let licls="";
let current="main"
let wcls="active"

let data

let q="Chennai"

let dbdata
let coordinates=[]
let c=[]

let lat, lon, jsonData

let mailSubject = 'Login Successful'
let mailText = 'You have successfully logged in to our website.'    

/* Register details */

let fname, lname, moblieNo, email, password, cpassword

/* Used to give an alert message using node */
const notifier = require('node-notifier');

const alert = require('alert')

/*PAYMENT*/


/*---------------------------------------------------------------------*/


app.get("/",function(req,res){

    wcls="active"
    licls=""
    locls="active"
    current="main"

    res.render("main",{wcls:wcls,licls:licls,locls:locls});

    connectMongoDB()
})

app.get("/about",function(req,res){
    if(!current.includes("home"))
        current="about"
    else{
        wcls="";
        licls="active"
        locls=""
    }
    res.render("about",{wcls:wcls,licls:licls,locls:locls});

})

app.get("/contact",function(req,res){
    if(!current.includes("home"))
        current="contact"
    else{
        wcls="";
        licls="active"
        locls=""
    }
    res.render("contact",{wcls:wcls,licls:licls,locls:locls});
})

app.get("/login",function(req,res){
    if(!current.includes("home"))
        current="login"
    else{
        wcls="active";
        licls=""
        locls="active"
    }
    let d1=req.headers.cookie
    c=d1.split('=')
    coordinates=c[1].split(',')
    lat=coordinates[0]
    lon=coordinates[1]
    const loc = {
        lat:lat,
        long:lon
    }

    fs.writeFileSync('C:/java_prog/chatbot-turf/chatbot-deployment-main/latlong.json',JSON.stringify(loc))
    res.render("login",{wcls:wcls,licls:licls,locls:locls});
})

app.post("/login",function(req,res){
    email = req.body.email
    password = req.body.password

    console.log(req.body);

    p=0

    dbname="admin"
    dbcollection = "login"

    getdetails(email,password).then(function(result){

        if(result.length == 0){
            alert("User does not exists")
            res.redirect("login")
        }
        else{    
            mailing(email, mailSubject, mailText);
            //console.log("here"+  jsonData[0].Direction)
            res.redirect("/home")
        }
    });
    try{
        fs.writeFileSync('C:/java_prog/chatbot-turf/chatbot-deployment-main/emailDetails.json',JSON.stringify(req.body))
        getdt()
    }catch(err){
        console.log(err)
    }
    current="home"

})

app.get("/home",function(req,res){
    if(current.includes("home")){
        res.render("home",{wcls:wcls, licls:licls, locls:locls, cards:jsonData, pageNum:1})
    }
    else{
        res.redirect("login")
    }  
})

/*card section*/
app.get('/home/:pageNum', (req, res) => {
    const cards = jsonData;
    const pageNum = parseInt(req.params.pageNum);
    const pageSize = 6;
    const startIdx = (pageNum - 1) * pageSize;
    const endIdx = startIdx + pageSize;
    const pageCards = cards.slice(startIdx, endIdx);
    res.render('home', { cards: pageCards, pageNum });
});

/**/

app.get("/weather",function(req,res){
    res.render("weather",{wcls:"",licls:"active",locls:"",datas:data});
})

app.post("/home",function(req,res){
    current="home"
//    console.log(req.body)
    res.render("home")
})

app.post("/weather",function(req,res){
    q=req.body.city
    datas=[]
    pre=0
    datas=getdt(q);
    res.setTimeout(2000,()=>{
        res.render("weather",{wcls:"",licls:"active",locls:"",datas:data})
    })
    
})


app.get("/register",function(req,res){
    if(!current.includes("home"))
        current="register"
    res.render("register");
})

app.post("/register",function(req,res){
    fname = req.body.fname
    lname = req.body.lname
    moblieNo = req.body.number
    email = req.body.email
    password = req.body.password

    dbname="admin"
    dbcollection = "register"


    getdetails(email,password).then(function(result){

        if(result.length == 0){
            dbcollection="register"
            insertintodb(fname, lname, moblieNo, email, password)
            dbcollection="login"
            insertintodb(email, password)
            
        }
        else{    
            alert('Already Registered...............\nTry login')
        }
    });    
    res.redirect("login");
    
})

app.get("/forgotpass",function(req,res){
    res.render("forgotpass");
        
})

app.post("/forgotpass",function(req,res){
    email = req.body.email
    password = req.body.password
    cpassword = req.body.cpassword
    console.log(req.body);
    dbname="admin"
    dbcollection = "register"
    if(!password.includes(cpassword)){
        alert("Password misatch.........")
        res.redirect("forgotpass")
    }
    else{
        getdetails(email).then(function(result){
            console.log("Results");
            if(result.length == 1){
                mailSubject = 'ALERT - Change in password!!!!!!' ;
                mailText = 'You have sccessfully changed your password. \nYour new password is '+cpassword ;
                mailing(email,mailSubject,mailText)
                updateDB(email,cpassword)
                dbcollection = 'login'
                updateDB(email,cpassword)
            }
        })
        res.redirect("login")
    }
})



app.listen(3000,function(req,res){
    console.log("listening..........");
})

async function getdt(){
    navigator.geolocation.getCurrentPosition( async position => {
        data=await getdata(lat, lon)
    })
}

async function getdata(){
    let dataa
    if(arguments.length==1){
        console.log("Args 1");
        let apik="http://api.openweathermap.org/data/2.5/forecast?q="+q+"&units=metric&appid=65cf4a6f2893592909c46c559ce10c40"
        let res=await fetch(apik)
        
        dataa = await res.json();
    }else{
        console.log("Args 2");
        let apik="http://api.openweathermap.org/data/2.5/forecast?lat="+lat+"&lon="+lon+"&appid=855010faa00e22d1d1338451814fc4a9"
        let res=await fetch(apik)
        dataa = await res.json();
    }
    console.log("Success");
    return dataa;
}

async function connectMongoDB(){
    result=await client.connect();
    db = result.db(dbname)
    
    Collection = db.collection(dbcollection)
    dbdata=await Collection.find({}).toArray();
}


async function insertintodb(){
    db = result.db(dbname)
    Collection = db.collection(dbcollection)
    if(arguments.length>2){
        Collection.insertOne({"fname":fname, "lname":lname, "moblieNo":moblieNo, "email":email, "password":password});
    }
    else if(arguments.length==2){
        Collection.insertOne({"email":email, "password":password});
    }
    else{
        dbdata=await Collection.find({}).toArray();
    }  
}

async function updateDB(email,password){
    db = result.db(dbname)
    Collection = db.collection(dbcollection)
    Collection.updateOne({"email":email}, {$set:{"password":password}});
}

async function getdetails(){
    result = await client.connect()
    db = result.db(dbname)
    Collection = db.collection(dbcollection)
    if(arguments.length == 2)
        dbdata = await Collection.find({email:email, password:password}).toArray();
    else
        dbdata = await Collection.find({email:email}).toArray();
    return dbdata
}

// mailing part



function mailing(email, mailSubject, mailText){
      
    const transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: {
            user: 'Your Email',
            pass: 'Your Password'
        }
    });
    
    const mailOptions = {
      from: 'Your Email',
      to: email,
      subject: mailSubject ,
      text: mailText
    };

    transporter.sendMail(mailOptions, function(error, info){
      if (error) {
        console.log(error);
      } else {
        console.log('Email sent');
      }
    });
}

fs.readFile(filePath, 'utf8', (err, data) => {
    try {
      jsonData = JSON.parse(data);
      //console.log('JSON data:', jsonData);
    } catch (parseError) {
      console.error('Error parsing JSON:', parseError);
    }
});
