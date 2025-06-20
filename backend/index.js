import express from "express"
import cors from "cors"
import axios from "axios"
const app=express();
app.use(cors())
app.use(express.json())

app.post("/getAns",async(req,res)=>{
    const question=req.body.question;
    const url=req.body.url;
    console.log(req.body)

    try{
        const response=await axios.post('http://localhost:5000/askIt',{
            url:url,
            question:question
        })

        console.log(response.data);

        return res.json(response.data.answer)
    }
    catch(err){
        console.log(err)
    }



    // const py= spawn('c:\\Users\\tony\\anaconda3\\envs\\custom_chatbot\\python.exe',["answerGeneration.py"]);

    // py.stdin.write(JSON.stringify({question:question,URLs:url}))
    // py.stdin.end()

    // let result = ''
    // py.stdout.on("data",(data)=>{
    //     result+=data.toString()
    // })
    // py.stderr.on("data", (err) => {
    //     console.error("Python Error:", err.toString())
    // })

    // py.on('close', () => {
    // try {
    //     const output = JSON.parse(result)
    //     console.log(output.answer)
    //     res.json(output.answer)
    //     } catch (e) {
    //     res.status(500).json({ error: 'Invalid JSON from Python' })
    //     }
    // })
})


app.listen(1234,()=>{
    console.log("Server is running")
})

