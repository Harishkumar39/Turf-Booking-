let dt=[]
let dataa, data

if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition( async position => {
        lat=position.coords.latitude;
        lon=position.coords.longitude;
        dt.push(lat)
        dt.push(lon)
        console.log(lat+" "+lon);
        document.cookie=`key=${dt}`
//        document.cookie = `location=${dt}; path=/home`
        dataa=await getdata(lat, lon)


    })
    
}



async function getdata(lat, lon){
    let apik="http://api.openweathermap.org/data/2.5/forecast?lat="+lat+"&lon="+lon+"&appid=855010faa00e22d1d1338451814fc4a9"
    let res=await fetch(apik)
    data = await res.json();
    console.log(data)
    return data;
}



//function preventBack(){window.history.forward();}
//    setTimeout(preventBack(), 0);
//    window.onunload=function(){null};
    
const pass = document.getElementById("password")
const cpass = document.getElementById("cpassword")
const b = document.getElementById("pass-icon")
const b1 = document.getElementById("pass-icon1")

const list=document.querySelector(".list-items")
// console.log("password"+c.value)

const togg = document.querySelector(".toggle")

togg.addEventListener("click",()=>{
    list.classList.toggle("active")
})

b.addEventListener('click', ()=> {
    if(pass.getAttribute("type")==="password")
        pass.setAttribute("type","text")
    
    else
        pass.setAttribute("type","password")
});

b1.addEventListener('click',()=>{
    if(cpass.getAttribute("type")==="password")
        cpass.setAttribute("type","text")
    else
        cpass.setAttribute("type","password")
})