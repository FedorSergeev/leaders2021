import { HttpHeaders } from '@angular/common/http';
import { HttpClient } from '@angular/common/http';
import { Component, SecurityContext } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import * as DOMPurify from 'dompurify';



@Component({
  selector: 'ngx-ecommerce',
  templateUrl: './rendered-map.component.html',
})
export class RenderedMapComponent {
  url: any = '';
  renderedMapEndpoint: string = "http://localhost:5000/social/api/v1.0/getpred"
  // renderedMapEndpoint: string = "http://localhost:5000/render_map"
  htmlData: any = '';
  htmlString: any = '';
  constructor(
    private sanitizer: DomSanitizer,
    private http: HttpClient
  ) { }

  ngOnInit() {
    this.url = this.sanitizer.bypassSecurityTrustResourceUrl("http://localhost:5000/render_map")
    this.getRenderedMap()
  }

  get processedDocument(): SafeHtml {
    if (this.htmlString) {
      const template = document.createElement('template');
      template.innerHTML = this.htmlString.trim()
      // const sanitized = DOMPurify.sanitize(this.htmlString, { ALLOWED_TAGS: ['meta', 'style', 'link', 'script'], RETURN_DOM: true });

      /* Add script tag */
      const script = document.createElement('script');
      script.src = 'assets/js/iframeResizer.contentWindow.js';
      template.content.appendChild(script)
      // sanitized.appendChild(script);

      /* Return result */
      // console.log("hey")
      // console.log(this.htmlString)
      // console.log(sanitized.outerHTML)
      return template.content.firstChild
    }
    return null;
  }

  public getRenderedMap() {
    const headers = new HttpHeaders({
      responseType: 'text/html',
      'Access-Control-Allow-Origin': '*'
    });

    // this.http.get<string>(this.renderedMapEndpoint, { headers })
    //   .subscribe(res => {
    //     // console.log(res)
    //     this.htmlString = res;
    //     // this.sanitizer.sanitize(SecurityContext.URL, url)
    //     this.htmlData = this.sanitizer.bypassSecurityTrustHtml(this.htmlString); // this line bypasses angular security
    //     console.log(this.htmlData)
    //   })

    this.http.get<SafeHtml>(this.renderedMapEndpoint, { headers })
      .subscribe(res => {
        console.log(res)
        this.htmlString = res;
        // this.htmlData = res
        // console.log(this.htmlData)
      })

  }
}
