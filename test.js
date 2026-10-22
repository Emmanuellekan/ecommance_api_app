const express = require("express");


const app = express()

app.use(express.json())

const courses = [
    { id: 1, name: 'course1'},
    { id: 2, name: 'course2'},
    { id: 3, name: 'course3'},
]

app.get('/', (req, res) => {
    res.send('Hello World')
})

app.get('/api/courses', (req, res) => {
    res.send(courses)
})

app.get('/api/courses/:id', (req, res) => {
    const course = courses.find(c => c.id === parseInt(req.params.id))

    if(!courses) res.status(404).send('The ID you asked for does not exist')

    res.send(course)
})

app.post('/api/courses', (req, res) => {
    const course = { 
        id: courses.length + 1,
        name: req.body.name
    }

    courses.push(course)
    res.send(course)
    
})


const PORT = process.env.PORT || 3000

app.listen(PORT, () => console.log(`Listen to server on ${PORT}...`))