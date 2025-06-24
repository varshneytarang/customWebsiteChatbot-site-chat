window.addEventListener("DOMContentLoaded",async()=>{
  // window.location.href="loader.html"
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const [{result}]=await chrome.scripting.executeScript({
    target:{tabId:tab.id},
    func:()=>{
      return document.body.innerText;
    }
  })
  console.log(result)
  const res=await fetch("http://localhost:5000/prepareIt",{
    method:"POST",
    headers: { "Content-Type": "application/json" },
    body:JSON.stringify({result})
  })
  const data=await res.json();

  if(data.msg=="Success"){
    document.body.classList.add("slide-out");
    setTimeout(() => {
    window.location.href = "popup.html";
    }, 800); // match the animation time
  }

})
