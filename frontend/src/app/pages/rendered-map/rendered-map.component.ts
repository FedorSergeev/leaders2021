import { HttpHeaders } from '@angular/common/http';
import { HttpClient } from '@angular/common/http';
import { Component } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';


@Component({
  selector: 'ngx-ecommerce',
  templateUrl: './rendered-map.component.html',
})
export class RenderedMapComponent {
  renderedMapEndpoint: string = "http://localhost:5000/render_map"
  htmlData: any = '';
  htmlString: any = '';
  constructor(
    private sanitizer: DomSanitizer,
    private http: HttpClient
  ) { }

  public getRenderedMap() {
    const headers = new HttpHeaders({
      'Content-Type': 'text/plain',
      responseType: 'text'
    });
    headers: new HttpHeaders({
      'Content-Type': 'text/plain',
      'Accept': 'text/plain'
    }),
      // this.http.get(this.myHtmlTemplate,{headers} ).subscribe((result)=>{
      //     console.log('got result',result);
      //       this.htmlData= result;
      //        this.htmlData = this.sanitizer.bypassSecurityTrustHtml(this.htmlString); // this line bypasses angular security
      // })

      this.http.get(this.renderedMapEndpoint, { responseType: 'text' }).subscribe(res => {
        this.htmlString = res;
        this.htmlData = this.sanitizer.bypassSecurityTrustHtml(this.htmlString); // this line bypasses angular security
      })
    // const request = this.http.get<string>('https://developer.mozilla.org/en-US/docs/Learn/HTML/Forms/Your_first_HTML_form', {
    //   headers: headers,
    //   responseType: 'text'
    // }).subscribe(res => this.htmlString = res);
    // }


  }
}
