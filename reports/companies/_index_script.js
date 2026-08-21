(function(){
  var toggle=document.getElementById('sidebarToggle'),
      wrap=document.getElementById('sidebarWrap'),
      mask=document.getElementById('sidebarMask');
  if(toggle) toggle.addEventListener('click',function(e){e.stopPropagation();wrap.classList.toggle('open');mask.classList.toggle('show');});
  if(mask) mask.addEventListener('click',function(){wrap.classList.remove('open');mask.classList.remove('show');});
  var links=document.querySelectorAll('.sidebar-nav a');
  links.forEach(function(l){l.addEventListener('click',function(e){
    var t=document.querySelector(this.getAttribute('href'));
    if(t){e.preventDefault();t.scrollIntoView({behavior:'smooth',block:'start'});}
    if(wrap.classList.contains('open')){wrap.classList.remove('open');mask.classList.remove('show');}
  });});
  var secs=document.querySelectorAll('.sec'), nl=document.querySelectorAll('.sidebar-nav a');
  window.addEventListener('scroll',function(){var cur='';
    secs.forEach(function(s){if(window.scrollY>=s.offsetTop-120)cur=s.id;});
    nl.forEach(function(l){l.classList.remove('active');if(l.getAttribute('href')==='#'+cur)l.classList.add('active');});
  });
})();