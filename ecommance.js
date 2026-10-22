const express = require('express')
const Joi = require('joi')
const app = express()


app.use(express.json())


app.get('/', (req, res) => {
    res.send()
})


const PORT = process.env.PORT || 3000

app.listen(PORT, () => console.log(`Server running ${PORT}...`))