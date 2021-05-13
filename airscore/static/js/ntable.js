/*
 * BSTable
 * @description  Javascript (JQuery) library to make bootstrap tables editable. Inspired by Tito Hinostroza's library Bootstable. BSTable Copyright (C) 2020 Thomas Rokicki
 * 
 * @version 1.0
 * @author Thomas Rokicki (CraftingGamerTom), Tito Hinostroza (t-edson)
 */

"use strict";

/** @class BSTable class that represents an editable bootstrap table. */
class NotificationsTable {

  /**
   * Creates an instance of BSTable.
   *
   * @constructor
   * @author: Thomas Rokicki (CraftingGamerTom)
   * @param {tableId} tableId The id of the table to make editable.
   * @param {options} options The desired options for the editable table.
   */
  constructor(tableId, pilot, options) {

    var defaults = {
      editableColumns: null,          // Index to editable columns. If null all td will be editable. Ex.: "1,2,3,4,5"
//      $addButton: null,               // Jquery object of "Add" button
      onEdit: function() {},          // Called after editing (accept button clicked)
      onBeforeDelete: function() {},  // Called before deletion
      onDelete: function() {},        // Called after deletion
      onAdd: function() {},           // Called when added a new row
      advanced: {                     // Do not override advanced unless you know what youre doing
        columnLabel: 'Actions',
        buttonHTML_delete: `<div class="btn-group pull-right">
            <button id="bDel" type="button" class="btn btn-sm btn-default">
              <span class="fas fa-trash-alt h6 text-dark" > </span>
            </button>
          </div>`,
        buttonHTML_edit_delete: `<div class="btn-group pull-right">
          <button id="bEdit" type="button" class="btn btn-sm btn-default">
            <span class="fas fa-edit h6 text-primary" > </span>
          </button>
          <button id="bDel" type="button" class="btn btn-sm btn-default">
            <span class="fas fa-trash-alt h6 text-dark" > </span>
          </button>
          <button id="bAcep" type="button" class="btn btn-sm btn-default" style="display:none;">
            <span class="fa fa-check h6 text-success" > </span>
          </button>
          <button id="bCanc" type="button" class="btn btn-sm btn-default" style="display:none;">
            <span class="fa fa-times h6 text-danger" > </span>
          </button>
          </div>`
      }
    };

    this.table = $('#' + tableId);
    this.data = pilot.notifications;

    if ( this.data.length ) {
      let jtg = this.data.find( el => el.notification_type == 'jtg' );
      this.jtg_penalty = jtg === undefined ? 0 : jtg.flat_penalty;
      let airspace = this.data.find( el => el.notification_type == 'auto' );
      this.perc_penalty = airspace === undefined ? 0 : airspace.percentage_penalty;
      let custom = this.data.find( el => el.notification_type == 'custom' );
      this.flat_penalty = custom === undefined ? 0 : custom.flat_penalty;
    }
    else {
      this.jtg_penalty = 0;
      this.perc_penalty = 0;
      this.flat_penalty = 0;
    }
    this.totalP = pilot.totalP;
    this.penalty = pilot.penalty;
    this.score = pilot.score;

    this.options = $.extend(true, defaults, options);

    //** @private */ this.actionsColumnHTML = '<td name="bstable-actions">' + this.options.advanced.buttonHTML + '</td>';

    //Process "editableColumns" parameter. Sets the columns that will be editable
    if (this.options.editableColumns != null) {
      // console.log("[DEBUG] editable columns: ", this.options.editableColumns);
      
      //Extract fields
      this.options.editableColumns = this.options.editableColumns.split(',');
    }
  }

  // --------------------------------------------------
  // -- Public Functions
  // --------------------------------------------------

  /**
   * Initializes the editable table. Creates the actions column.
   * @since 1.0.0
   */
  init() {
    let _this = this;
    this.table.DataTable({
      data: this.data,
      paging: false,
      destroy: true,
      searching: false,
      info: false,
      bSort: false,
      dom: 'tipB',
      buttons: {
        buttons: [
          {
            text: 'Add',
            attr:  {
              id: 'add_row'
            },
            action: function ( e, dt, node, config ) {
              let table = _this.table.DataTable();
//              console.log( 'Activated!' );
              _this._actionAddRow();
              $(table.row( ':last-child' ).nodes()).find('button[id=bEdit]').click();
            }
          }
        ]
      },
      columns: [
        {data: 'notification_type', title: 'Type'},
        {data: 'percentage_penalty', title:' Percentage'},
        {data: 'flat_penalty', title: 'Points'},
        {data: 'comment', title: 'Comment'},
        {data: 'notification_type', title: this.options.advanced.columnLabel, render: function (data) { return _this._create_row_buttons(data) }}
      ],
      language: {
        emptyTable: "No Penalties Found"
      },
      initComplete: function( data ) {
        $('#editmodal .modal-footer').show();
        _this._updateButtons();   // Add onclick events to each action button in all rows and toggle add row button state
      }
    });
  }

  /**
   * Destroys the editable table. Removes the actions column.
   * @since 1.0.0
   */
  destroy() {
    this.table.find('th[name="bstable-actions"]').remove(); //remove header
    this.table.find('td[name="bstable-actions"]').remove(); //remove body rows
  }

  /**
   * Refreshes the editable table. 
   *
   * Literally just removes and initializes the editable table again, wrapped in one function.
   * @since 1.0.0
   */
  refresh() {
    this.destroy();
    this.init();
  }

  // --------------------------------------------------
  // -- 'Static' Functions
  // --------------------------------------------------

  _create_row_buttons (notification_type) {
    if ( notification_type == 'jtg' ) return ''
    else if ( notification_type == 'auto' ) return this.options.advanced.buttonHTML_delete
    else return this.options.advanced.buttonHTML_edit_delete
  }

  _calculate_scores() {
    let new_not = [];
    let table =  this.table.DataTable();
    table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
      let data = this.data();
//      console.log(data);
      new_not.push( {
        notification_type: data.notification_type,
        percentage_penalty: data.percentage_penalty,
        flat_penalty: data.flat_penalty,
        comment: data.comment
      });
    });

    this.data = new_not;
    let penalty = 0
    if ( this.data.length ) {
      let airspace = this.data.find( el => el.notification_type == 'auto' );
      this.perc_penalty = airspace === undefined ? 0 : airspace.percentage_penalty;
      let custom = this.data.find( el => el.notification_type == 'custom' );
      this.flat_penalty = custom === undefined ? 0 : custom.flat_penalty;
      penalty = this.jtg_penalty + (this.totalP - this.jtg_penalty) * this.perc_penalty + this.flat_penalty;
    }
    this.score = Math.max(this.totalP - penalty, 0);
    this.penalty = this.totalP - this.score;
//    console.log([this.totalP, this.penalty, this.score]);
//    console.log(this.data)
  }

  _updateButtons() {
    this._addOnClickEventsToActions(); // Add onclick events to each action button in all rows
    this._addButtonState();   // toggle add row button state
  }

  _addButtonState() {
    if ( $('#bEdit').html() === undefined ) $('#add_row').prop('disabled', false);
    else $('#add_row').prop('disabled', true);
  }

  /**
   * Returns whether the provided row is currently being edited.
   *
   * @param {Object} row
   * @return {boolean} true if row is currently being edited.
   * @since 1.0.0
   */
  currentlyEditingRow($currentRow) {
    // Check if the row is currently being edited
    if ($currentRow.attr('data-status')=='editing') {
        return true;
    } else {
        return false;
    }
  }

  // --------------------------------------------------
  // -- Button Mode Functions
  // --------------------------------------------------

  _actionsModeNormal($currentRow) {
    $currentRow.find('#bAcep').hide();
    $currentRow.find('#bCanc').hide();
    $currentRow.find('#bEdit').show();
    $currentRow.find('#bDel').show();
    $currentRow.attr('data-status', '');               // remove editing status
  }
  _actionsModeEdit($currentRow) {
    $currentRow.find('#bAcep').show();
    $currentRow.find('#bCanc').show();
    $currentRow.find('#bEdit').hide();
    $currentRow.find('#bDel').hide();
    $currentRow.attr('data-status', 'editing');        // indicate the editing status
  }

  // --------------------------------------------------
  // -- Private Event Functions
  // --------------------------------------------------

  _rowEdit(rowIdx) {
  // Indicate user is editing the row
    let $currentRow = $(this.table.DataTable().row(rowIdx).node());
    let $cols = $currentRow.find('td');              // read rows
    if (this.currentlyEditingRow($currentRow)) return;    // not currently editing, return
    this._modifyEachColumn(this.options.editableColumns, $cols, function($td) {  // modify each column
      let content = $td.html();             // read content
      let div = '<div style="display: none;">' + content + '</div>';  // hide content (save for later use)
      let input = '<input class="form-control input-sm"  data-original-value="' + content + '" value="' + content + '">';
      $td.html(div + input);                // set content
    });
    this._actionsModeEdit($currentRow);
    $('#editmodal .modal-footer').hide();
  }
  _rowDelete(rowIdx) {
  // Remove the row
    let row = this.table.DataTable().row(rowIdx);
    this.options.onBeforeDelete(row);
    row.remove().draw();
    this._updateButtons();
    this._calculate_scores();
    this.options.onDelete();
  }
  _rowAccept(rowIdx) {
  // Accept the changes to the row
    let table = this.table.DataTable();
    let row = table.row(rowIdx);
    let $currentRow = $(row.node());
    if (!this.currentlyEditingRow($currentRow)) return;   // not currently editing, return
    let $cols = $currentRow.find('td');              // read fields

    
    // Finish editing the row & save edits
    this._modifyEachColumn(this.options.editableColumns, $cols, function($td) {  // modify each column
      let cont = $td.find('input').val();     // read through each input
      $td.html(cont);                         // set the content and remove the input fields
    });
    let data = row.data();
    data.flat_penalty = parseFloat($($cols[2]).html());
    data.comment = $($cols[3]).html();
    table.draw();
    this._calculate_scores();
    this._actionsModeNormal($currentRow);
    this.options.onEdit($currentRow);
    $('#editmodal .modal-footer').show();
  }
  _rowCancel(rowIdx) {
  // Reject the changes
    let $currentRow = $(this.table.DataTable().row(rowIdx).node());
    let row = this.table.DataTable().row(rowIdx);
    if (!this.currentlyEditingRow($currentRow)) return;   // not currently editing, return
    let $cols = $currentRow.find('td');              // read fields


    // Finish editing the row & delete changes
    this._modifyEachColumn(this.options.editableColumns, $cols, function($td) {  // modify each column
      let cont = $td.find('div').html();    // read div content
      $td.html(cont);                       // set the content and remove the input fields
    });
    this._actionsModeNormal($currentRow);
    $('#editmodal .modal-footer').show();
  }
  _actionAddRow() {
    // Add row to this table
    let table = this.table.DataTable();
    table.row.add( {
      notification_type:  "custom",
      percentage_penalty: 0,
      flat_penalty:       0,
      comment:            "",
      null:               this._create_row_buttons('custom')
    } ).draw();
    this._updateButtons();

    this._addOnClickEventsToActions(); // Add onclick events to each action button in all rows
    this.options.onAdd();
  }

  // --------------------------------------------------
  // -- Helper Functions
  // --------------------------------------------------

  _modifyEachColumn($editableColumns, $cols, howToModify) {
  // Go through each editable field and perform the howToModifyFunction function
    let n = 0;
    $cols.each(function() {
      n++;
      if ($(this).attr('name')=='bstable-actions') return;    // exclude the actions column
      if (!isEditableColumn(n-1)) return;                     // Check if the column is editable
      howToModify($(this));                                   // If editable, call the provided function
    });

    function isEditableColumn(columnIndex) {
    // Indicates if the column is editable, based on configuration
        if ($editableColumns==null) {                           // option not defined
            return true;                                        // all columns are editable
        } else {                                                // option is defined
            //console.log('isEditableColumn: ' + columnIndex);  // DEBUG
            for (let i = 0; i < $editableColumns.length; i++) {
              if (columnIndex == $editableColumns[i]) return true;
            }
            return false;  // column not found
        }
    }
  }

  _addOnClickEventsToActions() {
    let _this = this;
    // Add onclick events to each action button
    let table =  this.table.DataTable();
    table.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
      let row = $(this.node());
      row.find('#bEdit').each(function() {let button = this; button.onclick = function() {_this._rowEdit(rowIdx)} });
      row.find('#bDel').each(function() {let button = this; button.onclick = function() {_this._rowDelete(rowIdx)} });
      row.find('#bAcep').each(function() {let button = this; button.onclick = function() {_this._rowAccept(rowIdx)} });
      row.find('#bCanc').each(function() {let button = this; button.onclick = function() {_this._rowCancel(rowIdx)} });
    });
  }

  // --------------------------------------------------
  // -- Conversion Functions
  // --------------------------------------------------

  convertTableToCSV(separator) {  
  // Convert table to CSV
    let _this = this;
    let $currentRowValues = '';
    let tableValues = '';

    _this.table.find('tbody tr').each(function() {
        // force edits to complete if in progress
        if (_this.currentlyEditingRow($(this))) {
            $(this).find('#bAcep').click();       // Force Accept Edit
        }
        let $cols = $(this).find('td');           // read columns
        $currentRowValues = '';
        $cols.each(function() {
            if ($(this).attr('name')=='bstable-actions') {
                // buttons column - do nothing
            } else {
                $currentRowValues = $currentRowValues + $(this).html() + separator;
            }
        });
        if ($currentRowValues!='') {
            $currentRowValues = $currentRowValues.substr(0, $currentRowValues.length-separator.length); 
        }
        tableValues = tableValues + $currentRowValues + '\n';
    });
    return tableValues;
  }

}

