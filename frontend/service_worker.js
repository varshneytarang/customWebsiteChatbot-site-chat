
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
    if (!tab.url) return;
    const url = new URL(tab.url);
        await chrome.sidePanel.setOptions({
        tabId,
        path: 'intro.html',
        enabled: true,
    });  
    document.getElementById("question").disabled = true;



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
        document.getElementById("question").disabled = false;
    }    

});


