import { Component, input } from '@angular/core';
@Component({ selector: 'app-ui-state', template: `<section class="ui-state" [attr.role]="kind() === 'error' ? 'alert' : null"><h2>{{ title() }}</h2><p>{{ message() }}</p></section>` })
export class UiStateComponent { readonly kind = input<'loading' | 'empty' | 'error'>('empty'); readonly title = input.required<string>(); readonly message = input.required<string>(); }
