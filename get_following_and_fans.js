'use strict';
var cheerio = require('cheerio')
var fs = require('fs')

const folder = process.argv[2]
const timeStr = process.argv[3]
const folderPath = folder + '/' + timeStr

const totalPageNum = parseInt(process.argv[4])
const jsonPath = folderPath + '/' + folder + '__filted.json'

// console.log('js begin ... ...')
// console.log('folderPath: ' + folderPath)
// console.log('totalPageNum: ' + totalPageNum)

var arr = []

for (let i = 1; i <= totalPageNum; ++i) {
    let htmlPath = folderPath + '/' + folder + '__' + ('000'+i).substr(-3) + '.html'
    
    var data = fs.readFileSync(htmlPath).toString()

    var $ = cheerio.load(data);
    $('table').each(function(index, el) {
        let a = $(el).find('a').eq(1)
        let username = a.text()
        let userid = parseInt(a.attr('href').split('/').pop())
        if (!userid) {
            let href = $(el).find('a').eq(2).attr('href')
            let patt = /\d{8,12}/g
            userid = parseInt(href.match(patt)[0])
        }
        arr.push([username, userid])
    })

}

var txt = JSON.stringify(arr, null, 4)

fs.writeFile(jsonPath, txt,  function(err) {
   if (err) {
       return console.error(err);
   }
   console.log('saving ' + jsonPath)
});