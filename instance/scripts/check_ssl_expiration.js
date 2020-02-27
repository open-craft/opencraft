var request = require('request');  

/* 
************************************************** 
What is the URL that you want to check? 
************************************************** 
*/ 
var urlToMonitor = 'https://example.com'; 
console.log('Preparing to monitor '+urlToMonitor);  

/* 
************************************************** 
How many days before your certification expires do you want this monitor to fail?  
I.e. daysBeforeExpiration = 2 
This monitor will start failing within 2 days of the SSL certificate expiring 
************************************************** 
*/
var daysBeforeExpiration = 2; 
console.log('This monitor will fail if the SSL certificate expires within the next '+daysBeforeExpiration+' days...');  

var r = request({   
    url: urlToMonitor,   
    method: 'HEAD',   
    gzip: true,   
    followRedirect: false,      
    followAllRedirects: false 
});  

r.on('response', 
    function(res) {   
        var certDetails = (res.req.connection.getPeerCertificate());   
        var expirationDate = new Date(certDetails.valid_to);   
        var certificateIssuer = certDetails.issuer.O;
        //   
        console.log('This certificate was issued by '+certificateIssuer, '');   
        console.log('This SSL certificate will expire on '+expirationDate, '');   
        //   
        //Let's offset the failure date by the user supplied daysBeforeExpiration   
        expirationDate.setDate(expirationDate.getDate() - daysBeforeExpiration);   
        //   
        var currentDate = new Date();   
        //   
        console.log('**** Offset expiration date: '+expirationDate);   
        console.log('**** Date at time of testing: '+currentDate);   
        //   
        if(expirationDate < currentDate){     
           throw new Error('The test has FAILED as the offset expiration date is before now!');   
        }else{     
           console.log('The test is a SUCCESS, the expiration date is after now...');   
        } 
    }
);