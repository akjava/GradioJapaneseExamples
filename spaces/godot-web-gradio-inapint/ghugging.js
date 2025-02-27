

GHugging ={}
window.Ghugging = GHugging
  //console.log(window.huggingface)

  GHugging.signin_huggingface = async function signin_huggingface() {
      console.log("signin_huggingface called")
      // prompt=consent to re-trigger the consent screen instead of silently redirecting
      window.location.href = (await oauthLoginUrl({scope:window.huggingface.variables.OAUTH_SCOPES})) + "&prompt=consent";
    };
  
    GHugging.signout_huggingface =  function signout_huggingface() {
      console.log("signout_hugginfface called")
      console.log(localStorage)
      localStorage.removeItem("oauth");
      console.log("removed")
      window.location.href = window.location.href.replace(/\?.*$/, '');
      window.location.reload();
    };
    GHugging.get_huggingface_oauth = async function get_huggingface_oauth(_js_callback){
      //console.log("huggingface env", window.huggingface);

      let oauthResult = localStorage.getItem("oauth");

      if (oauthResult) {
      try {
          oauthResult = JSON.parse(oauthResult);
      } catch {
          oauthResult = null;
      }
      }
      
      var host_name = window.location.hostname
      if (host_name!="localhost" & host_name!="127.0.0.1"){
      //typeof window.huggingface!='undefined'
         console.log("on hugging face")
         //console.log(typeof window.huggingface)
         
          oauthResult ||= await oauthHandleRedirectIfPresent();
          
          _js_callback(oauthResult)
      }else{
          console.log("on localhost")
          //must  be local
          GHugging.load_local_token(_js_callback)
      }
      

  }
  GHugging.load_local_token = function(_js_callback){
      var xhr = new XMLHttpRequest();
      xhr.open('GET', '/env.json', true);
      xhr.responseType = 'json';

      xhr.onload = function() {
      var status = xhr.status;
      if (status === 200) {
          //console.log(xhr.response);
          _js_callback({"accessToken":xhr.response["hf_token"]})
      } else {
          console.error('Error:', status);
      }
      };

      xhr.onerror = function() {
          console.error('Request failed');
      };

      xhr.send();
  }
